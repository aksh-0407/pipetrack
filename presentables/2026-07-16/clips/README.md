# Before / after clips

Four matched pairs, same delivery in each. "before" is PIPETRACK V8.0, "after" is the current pipeline.
All files are H.264 (yuv420p, faststart), so they play on a phone and on WhatsApp.

File naming: `<delivery>__before_V8.0.mp4` and `<delivery>__after_current.mp4`.

| Delivery | Before file | After file | Cross-camera agreement | What to look at |
|---|---|---|---|---|
| M1_1_14_1 | M1_1_14_1__before_V8.0.mp4 | M1_1_14_1__after_current.mp4 | 0.798 to 0.933 | Clean clip. Current is steadier with more consistent IDs. Shows an easy case improving without regressing. |
| M1_1_14_3 | M1_1_14_3__before_V8.0.mp4 | M1_1_14_3__after_current.mp4 | 0.882 to 0.935 | Busy crease. Handled cleanly in the current build. |
| M2_1_12_1 | M2_1_12_1__before_V8.0.mp4 | M2_1_12_1__after_current.mp4 | 0.886 to 0.925 | Biggest visible improvement. V8 had 184 marker teleports on this clip; the current build has 0. Watch the busy passage where the old markers jump across the field. |
| M1_1_14_7 | M1_1_14_7__before_V8.0.mp4 | M1_1_14_7__after_current.mp4 | 0.811 to 0.831 | The hardest case. Low-parallax facing-pair geometry. Improved but still our main remaining challenge, shown honestly. |

Notes:
- The current clips use the updated labels: each ID chip is filled with that player's own colour with
  high-contrast text, and the line from a label to its box is thicker, so a label is easy to trace to the
  correct player.
- Full numbers for all 8 deliveries are in ../CONSOLIDATED_RESULTS.md.
