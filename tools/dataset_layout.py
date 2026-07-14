#!/usr/bin/env python3
"""Analyse the layout, contents and structure of an *arbitrary* dataset dir.

This tool makes NO assumptions about what the dataset contains. It discovers
everything empirically by walking the tree, and it is a single self-contained
file using only the Python standard library, so you can copy it to any machine
(`python3 dataset_layout.py /path/to/data`) and run it with no dependencies.

The point is not to `ls` every file -- a data folder can hold thousands of
near-identical items. Instead it accounts for every file exactly once while
collapsing repetition into human-readable patterns, so you can understand:

  * how the folder tree is arranged (depth, fan-out),
  * what KINDS of data live where -- detected by extension AND by content
    (magic bytes), not by guessing from names,
  * how MUCH of each there is (counts + on-disk size),
  * sequenced / numbered files collapsed into one pattern with its index range,
  * repeated sub-directory structures collapsed into "N dirs like this",
  * the SHAPE of structured files (JSON keys, JSONL/CSV rows & columns),
  * a content sample for unrecognised file types.

Nothing is hidden -- items are only grouped. Totals always cover 100% of files.

Usage:
    python3 dataset_layout.py ROOT [options]

Options:
    --tree                 print the full tree with files collapsed to patterns
    --peek                 describe the shape/content of structured & unknown files
    --collapse-threshold N collapse N+ identical sibling dirs in --tree (default 3)
    --peek-max-bytes N     skip content-peeking files larger than N bytes (default 64MiB)
    --follow-symlinks      descend into symlinked directories (off by default)
    -o FILE                write the report to FILE instead of stdout
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

# Runs of digits are what vary inside a sequence, so we template them out to
# group filenames. "frame_000212448.jpg" -> "frame_#########.jpg", and every
# sibling frame lands in the same bucket.
_DIGIT_RUN = re.compile(r"\d+")

# Extension -> coarse kind. Only used as a hint; content sniffing (below) is the
# authoritative signal for what a file actually is.
_EXT_KIND = {
    **{e: "image" for e in (".jpg", ".jpeg", ".png", ".bmp", ".gif",
                            ".tif", ".tiff", ".webp", ".exr", ".ppm")},
    **{e: "video" for e in (".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv")},
    **{e: "audio" for e in (".wav", ".mp3", ".flac", ".ogg", ".m4a")},
    **{e: "table" for e in (".csv", ".tsv", ".parquet", ".feather", ".arrow")},
    **{e: "json" for e in (".json", ".jsonl", ".ndjson", ".geojson")},
    **{e: "array" for e in (".npy", ".npz", ".pt", ".pth", ".pkl",
                            ".pickle", ".h5", ".hdf5", ".mat", ".safetensors")},
    **{e: "text" for e in (".txt", ".md", ".yaml", ".yml", ".xml", ".ini",
                           ".cfg", ".log", ".rst")},
    **{e: "archive" for e in (".zip", ".tar", ".gz", ".tgz", ".bz2", ".xz",
                              ".7z", ".rar")},
}

# Leading magic bytes -> content kind. This is how we characterise files whose
# extension is missing, wrong, or unfamiliar.
_MAGIC = [
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"GIF8", "image/gif"),
    (b"BM", "image/bmp"),
    (b"II*\x00", "image/tiff"),
    (b"MM\x00*", "image/tiff"),
    (b"RIFF", "riff (wav/avi/webp)"),
    (b"\x00\x00\x00\x18ftyp", "video/mp4"),
    (b"\x00\x00\x00\x20ftyp", "video/mp4"),
    (b"\x1a\x45\xdf\xa3", "video/matroska-webm"),
    (b"\x93NUMPY", "numpy .npy"),
    (b"PK\x03\x04", "zip (npz/parquet/xlsx/...)"),
    (b"\x1f\x8b", "gzip"),
    (b"BZh", "bzip2"),
    (b"\xfd7zXZ\x00", "xz"),
    (b"7z\xbc\xaf\x27\x1c", "7z"),
    (b"\x89HDF\r\n\x1a\n", "hdf5"),
    (b"SQLite format 3\x00", "sqlite3"),
    (b"\x80\x04", "python pickle (proto 4)"),
    (b"\x80\x05", "python pickle (proto 5)"),
    (b"PAR1", "parquet"),
]


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def human_size(n: int) -> str:
    step = 1024.0
    v = float(n)
    for unit in ("B", "KB", "MB", "GB", "TB", "PB"):
        if v < step or unit == "PB":
            return f"{int(v)} {unit}" if unit == "B" else f"{v:.1f} {unit}"
        v /= step
    return f"{v:.1f} PB"


def template_name(name: str) -> str:
    """Replace each run of digits with the same number of '#' characters."""
    return _DIGIT_RUN.sub(lambda m: "#" * len(m.group()), name)


def sniff_content(path: Path) -> str:
    """Best-effort file-type identification from the first bytes."""
    try:
        with path.open("rb") as fh:
            head = fh.read(64)
    except OSError:
        return "unreadable"
    if not head:
        return "empty"
    for sig, label in _MAGIC:
        if head.startswith(sig):
            return label
    # printable-ASCII heuristic -> text
    printable = sum(1 for b in head if 9 <= b <= 13 or 32 <= b <= 126)
    if printable / len(head) > 0.90:
        return "text"
    return "binary"


def ext_kind(ext: str) -> str:
    return _EXT_KIND.get(ext, "other")


# --------------------------------------------------------------------------- #
# per-directory model
# --------------------------------------------------------------------------- #
@dataclass
class FilePattern:
    template: str
    ext: str
    count: int = 0
    total_size: int = 0
    example: str = ""
    numbers: list[int] = field(default_factory=list)  # varying index, if unambiguous

    def numeric_range(self) -> str:
        if not self.numbers:
            return ""
        lo, hi = min(self.numbers), max(self.numbers)
        span = hi - lo + 1
        gaps = span - len(set(self.numbers))
        rng = f"{lo}..{hi}"
        if gaps > 0:
            rng += f", {gaps} gaps in {span}"
        return rng


@dataclass
class DirInfo:
    path: Path
    subdirs: list[str] = field(default_factory=list)
    patterns: dict[str, FilePattern] = field(default_factory=dict)
    file_count: int = 0
    total_size: int = 0

    def add_file(self, name: str, size: int) -> None:
        ext = Path(name).suffix.lower()
        tmpl = template_name(name)
        pat = self.patterns.get(tmpl)
        if pat is None:
            pat = FilePattern(template=tmpl, ext=ext, example=name)
            self.patterns[tmpl] = pat
        pat.count += 1
        pat.total_size += size
        # capture the varying index only when exactly one digit-run varies
        # (otherwise it's ambiguous which run is the sequence counter)
        runs = _DIGIT_RUN.findall(name)
        if len(re.findall(r"#+", tmpl)) == 1 and len(runs) == 1:
            try:
                pat.numbers.append(int(runs[0]))
            except ValueError:
                pass
        self.file_count += 1
        self.total_size += size

    def signature(self) -> tuple:
        """Structural fingerprint: child dir names + file patterns (no counts)."""
        pats = tuple(sorted((p.template, p.ext) for p in self.patterns.values()))
        return (tuple(sorted(self.subdirs)), pats)


# --------------------------------------------------------------------------- #
# scanning
# --------------------------------------------------------------------------- #
def scan(root: Path, follow_symlinks: bool) -> tuple[dict[Path, DirInfo], list[str]]:
    dirs: dict[Path, DirInfo] = {}
    warnings: list[str] = []

    def on_error(exc: OSError) -> None:
        warnings.append(f"cannot access {getattr(exc, 'filename', '?')}: {exc.strerror}")

    for dirpath, dirnames, filenames in os.walk(root, onerror=on_error,
                                                followlinks=follow_symlinks):
        dirnames.sort()
        p = Path(dirpath)
        info = DirInfo(path=p, subdirs=sorted(dirnames))
        for fn in filenames:
            fp = p / fn
            try:
                # lstat: count symlinks themselves, don't chase them into totals
                size = fp.lstat().st_size
            except OSError:
                size = 0
            info.add_file(fn, size)
        dirs[p] = info
    return dirs, warnings


def aggregate_size(root: Path, dirs: dict[Path, DirInfo]) -> dict[Path, int]:
    totals: dict[Path, int] = defaultdict(int)
    for p in sorted(dirs, key=lambda x: len(x.parts), reverse=True):
        totals[p] += dirs[p].total_size
        if p != root and p.parent in dirs:
            totals[p.parent] += totals[p]
    return totals


# --------------------------------------------------------------------------- #
# structured / unknown file peeking
# --------------------------------------------------------------------------- #
def _describe_value(data, max_keys: int = 12) -> str:
    if isinstance(data, dict):
        keys = list(map(str, data.keys()))
        shown = keys[:max_keys]
        extra = f" (+{len(keys) - len(shown)} more)" if len(keys) > len(shown) else ""
        return f"dict[{len(keys)} keys]: {', '.join(shown)}{extra}"
    if isinstance(data, list):
        head = data[0] if data else None
        inner = ""
        if isinstance(head, dict):
            inner = " of dict{" + ", ".join(map(str, list(head.keys())[:6])) + "}"
        elif head is not None:
            inner = f" of {type(head).__name__}"
        return f"list[{len(data)}]{inner}"
    return type(data).__name__


def peek(path: Path, max_bytes: int) -> str:
    """Describe a file's shape/content without assuming what it is."""
    try:
        size = path.lstat().st_size
    except OSError:
        return "[unreadable]"
    ext = path.suffix.lower()

    if ext in (".json", ".geojson"):
        if size > max_bytes:
            return f"json, {human_size(size)} (too large to parse; use --peek-max-bytes)"
        try:
            with path.open() as fh:
                return _describe_value(json.load(fh))
        except Exception as exc:  # noqa: BLE001
            return f"json [parse error: {exc.__class__.__name__}]"

    if ext in (".jsonl", ".ndjson"):
        try:
            with path.open() as fh:
                first = fh.readline()
                n = 1 + sum(1 for _ in fh) if first else 0
            return f"jsonl[{n} lines], first: {_describe_value(json.loads(first))}" \
                if first else "jsonl [empty]"
        except Exception as exc:  # noqa: BLE001
            return f"jsonl [error: {exc.__class__.__name__}]"

    if ext in (".csv", ".tsv"):
        sep = "\t" if ext == ".tsv" else ","
        try:
            with path.open() as fh:
                header = fh.readline().rstrip("\n")
                n = 1 + sum(1 for _ in fh) if header else 0
            cols = header.split(sep)
            head = ", ".join(cols[:8]) + (f" (+{len(cols) - 8} cols)" if len(cols) > 8 else "")
            return f"{ext[1:]}[{n} rows, {len(cols)} cols]: {head}"
        except Exception as exc:  # noqa: BLE001
            return f"{ext[1:]} [error: {exc.__class__.__name__}]"

    # unknown / binary -> sniff magic bytes, and show first text line if textual
    content = sniff_content(path)
    if content == "text":
        try:
            with path.open(errors="replace") as fh:
                line = fh.readline().strip()
            snippet = (line[:80] + "...") if len(line) > 80 else line
            return f"text, {human_size(size)}, first line: {snippet!r}"
        except OSError:
            return f"text, {human_size(size)}"
    return f"{content}, {human_size(size)}"


# --------------------------------------------------------------------------- #
# reporting
# --------------------------------------------------------------------------- #
class Report:
    def __init__(self) -> None:
        self.lines: list[str] = []

    def __call__(self, s: str = "") -> None:
        self.lines.append(s)

    def text(self) -> str:
        return "\n".join(self.lines)


def _is_within(p: Path, base: Path) -> bool:
    return p == base or base in p.parents


def summarise(root: Path, args: argparse.Namespace) -> str:
    dirs, warnings = scan(root, args.follow_symlinks)
    tree_size = aggregate_size(root, dirs)
    out = Report()

    total_files = sum(d.file_count for d in dirs.values())
    total_bytes = sum(d.total_size for d in dirs.values())
    max_depth = max((len(p.relative_to(root).parts) for p in dirs), default=0)

    ext_count: Counter = Counter()
    ext_bytes: Counter = Counter()
    kind_count: Counter = Counter()
    kind_bytes: Counter = Counter()
    for d in dirs.values():
        for pat in d.patterns.values():
            key = pat.ext or "(no ext)"
            ext_count[key] += pat.count
            ext_bytes[key] += pat.total_size
            kind_count[ext_kind(pat.ext)] += pat.count
            kind_bytes[ext_kind(pat.ext)] += pat.total_size

    out("=" * 78)
    out(f"DATASET ANALYSIS  ::  {root}")
    out("=" * 78)
    out(f"directories : {len(dirs)}")
    out(f"files       : {total_files}")
    out(f"total size  : {human_size(total_bytes)}")
    out(f"max depth   : {max_depth} levels below root")
    out(f"empty       : {sum(1 for d in dirs.values() if d.file_count == 0)} dirs with no files")
    if warnings:
        out(f"warnings    : {len(warnings)} (access errors -- see end)")
    out()
    out("by kind (extension-based):")
    for kind, c in kind_count.most_common():
        out(f"  {kind:<10} {c:>8} files   {human_size(kind_bytes[kind]):>10}")
    out()
    out("by extension:")
    for ext, c in ext_count.most_common():
        out(f"  {ext:<12} {c:>8} files   {human_size(ext_bytes[ext]):>10}")
    out()

    # ---- content-type verification (sniff a sample per extension) -------- #
    _report_content_types(root, dirs, out)

    # ---- top-level breakdown -------------------------------------------- #
    out("-" * 78)
    out("TOP-LEVEL BREAKDOWN")
    out("-" * 78)
    top = dirs[root]
    if not top.subdirs and not top.patterns:
        out("  (root is empty)")
    for sub in top.subdirs:
        sp = root / sub
        n_files = sum(d.file_count for p, d in dirs.items() if _is_within(p, sp))
        n_dirs = sum(1 for p in dirs if _is_within(p, sp) and p != sp)
        out(f"  {sub}/   {n_files} files, {n_dirs} sub-dirs, {human_size(tree_size[sp])}")
    for pat in top.patterns.values():
        out(f"  {pat.example}   ({pat.count}x, {human_size(pat.total_size)})")
    out()

    # ---- repeated structure --------------------------------------------- #
    _report_repeated_groups(root, dirs, out)

    # ---- structured/unknown peek ---------------------------------------- #
    if args.peek:
        _report_peek(root, dirs, out, args.peek_max_bytes)

    # ---- full tree ------------------------------------------------------ #
    if args.tree:
        out("-" * 78)
        out("DIRECTORY TREE  (files collapsed to patterns, identical dirs collapsed)")
        out("-" * 78)
        _print_tree(root, root, dirs, tree_size, out, args, prefix="")
        out()

    if warnings:
        out("-" * 78)
        out("WARNINGS")
        out("-" * 78)
        for w in warnings[:50]:
            out(f"  {w}")
        if len(warnings) > 50:
            out(f"  ... and {len(warnings) - 50} more")

    return out.text()


def _report_content_types(root: Path, dirs: dict[Path, DirInfo], out: Report) -> None:
    """Sniff one representative file per extension to verify what it really is."""
    rep: dict[str, Path] = {}
    for p in sorted(dirs):
        for pat in dirs[p].patterns.values():
            key = pat.ext or "(no ext)"
            rep.setdefault(key, p / pat.example)
    out("-" * 78)
    out("CONTENT-TYPE CHECK  (magic-byte sniff of one file per extension)")
    out("-" * 78)
    for ext in sorted(rep):
        sniff = sniff_content(rep[ext])
        out(f"  {ext:<12} -> {sniff:<24}  e.g. {rep[ext].relative_to(root)}")
    out()


def _report_repeated_groups(root: Path, dirs: dict[Path, DirInfo], out: Report) -> None:
    out("-" * 78)
    out("REPEATED STRUCTURE  (identical sibling directories collapsed)")
    out("-" * 78)
    reported = False
    for parent in sorted(dirs, key=lambda x: len(x.parts)):
        info = dirs[parent]
        child_dirs = [parent / s for s in info.subdirs if (parent / s) in dirs]
        if len(child_dirs) < 2:
            continue
        groups: dict[tuple, list[Path]] = defaultdict(list)
        for c in child_dirs:
            groups[dirs[c].signature()].append(c)
        for sig, members in groups.items():
            if len(members) < 2:
                continue
            reported = True
            rel = parent.relative_to(root) if parent != root else Path(".")
            out(f"  {rel}/  ->  {len(members)} directories with identical structure:")
            out(f"      e.g. {', '.join(m.name for m in members[:6])}"
                + (" ..." if len(members) > 6 else ""))
            sub_dirs, _ = sig
            if sub_dirs:
                out(f"      each contains sub-dirs: {', '.join(sub_dirs)}")
            rep = dirs[members[0]]
            for pat in sorted(rep.patterns.values(), key=lambda x: x.template):
                rng = f"  [{pat.numeric_range()}]" if pat.numeric_range() else ""
                out(f"      each has: {pat.template}  ({pat.count}x per dir){rng}")
            out()
    if not reported:
        out("  (none detected)")
        out()


def _report_peek(root: Path, dirs: dict[Path, DirInfo], out: Report, max_bytes: int) -> None:
    out("-" * 78)
    out("FILE SHAPES  (one representative per pattern per directory)")
    out("-" * 78)
    shown = 0
    for p in sorted(dirs):
        for pat in dirs[p].patterns.values():
            rel = (p / pat.example).relative_to(root)
            desc = peek(p / pat.example, max_bytes)
            note = f"  (pattern x{pat.count})" if pat.count > 1 else ""
            out(f"  {rel}{note}")
            out(f"      {desc}")
            shown += 1
    if shown == 0:
        out("  (no files)")
    out()


def _print_tree(root: Path, cur: Path, dirs: dict[Path, DirInfo],
                tree_size: dict[Path, int], out: Report,
                args: argparse.Namespace, prefix: str) -> None:
    info = dirs[cur]
    out(f"{prefix}{cur.name or str(root)}/   "
        f"[{info.file_count} files here, {human_size(tree_size[cur])} total]")
    child_prefix = prefix + "    "
    for pat in sorted(info.patterns.values(), key=lambda x: (-x.count, x.template)):
        rng = f"  [{pat.numeric_range()}]" if pat.numeric_range() else ""
        if pat.count > 1:
            out(f"{child_prefix}{pat.template}  "
                f"x{pat.count}, {human_size(pat.total_size)}{rng}")
        else:
            out(f"{child_prefix}{pat.example}  ({human_size(pat.total_size)})")
    child_dirs = [cur / s for s in info.subdirs if (cur / s) in dirs]
    groups: dict[tuple, list[Path]] = defaultdict(list)
    for c in child_dirs:
        groups[dirs[c].signature()].append(c)
    for c in child_dirs:
        members = groups[dirs[c].signature()]
        if len(members) >= args.collapse_threshold and c is not members[0]:
            continue
        if len(members) >= args.collapse_threshold and c is members[0]:
            out(f"{child_prefix}[{len(members)} identical dirs: "
                f"{members[0].name} ... {members[-1].name}] -- showing one:")
        _print_tree(root, c, dirs, tree_size, out, args, child_prefix)


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", help="dataset root directory to analyse")
    ap.add_argument("--tree", action="store_true",
                    help="print full tree with files collapsed to patterns")
    ap.add_argument("--peek", action="store_true",
                    help="describe shape/content of structured & unknown files")
    ap.add_argument("--collapse-threshold", type=int, default=3,
                    help="collapse N+ identical sibling dirs in --tree (default 3)")
    ap.add_argument("--peek-max-bytes", type=int, default=64 * 1024 * 1024,
                    help="skip content-parsing files larger than this (default 64MiB)")
    ap.add_argument("--follow-symlinks", action="store_true",
                    help="descend into symlinked directories (off by default)")
    ap.add_argument("-o", "--output", help="write report to file instead of stdout")
    args = ap.parse_args(argv)

    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2

    report = summarise(root, args)
    if args.output:
        Path(args.output).write_text(report + "\n")
        print(f"wrote {args.output} ({len(report.splitlines())} lines)")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
