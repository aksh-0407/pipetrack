# PIPETRACK V8.0 vs Current: consolidated results

Same 8 deliveries, same metrics, measured the same way. Change vs V8.0 shown in parentheses.

## Summary (mean over the 8 deliveries)

| Parameter | V8.0 | Current |
|---|---|---|
| Cross-camera agreement (higher is better) | 0.782 | 0.916 (+0.134) |
| Worst-clip agreement | 0.477 | 0.831 (+0.354) |
| Visible teleport markers (total) | 422 | 0 (-422) |
| Peak teleports in one clip | 184 | 0 (-184) |
| Distinct IDs per clip (roster is about 11) | 12.6 | 10.6 (-2.0) |
| Same-camera ID collisions (must be 0) | 0 | 0 (0) |
| Colocated ghost-ID pairs | present | 0 |
| Triangulation reprojection error (px) | 3.3 | 3.3 (0) |

## Per delivery

| Delivery | V8.0 agreement | Current agreement | V8.0 teleports | Current teleports |
|---|---|---|---|---|
| M1_1_14_1 | 0.798 | 0.933 (+0.135) | 7 | 0 |
| M1_1_14_2 | 0.802 | 0.921 (+0.119) | 3 | 0 |
| M1_1_14_3 | 0.882 | 0.935 (+0.053) | 70 | 0 |
| M1_1_14_4 | 0.972 | 0.975 (+0.003) | 20 | 0 |
| M1_1_14_5 | 0.627 | 0.902 (+0.275) | 30 | 0 |
| M1_1_14_6 | 0.477 | 0.906 (+0.429) | 53 | 0 |
| M1_1_14_7 | 0.811 | 0.831 (+0.020) | 55 | 0 |
| M2_1_12_1 | 0.886 | 0.925 (+0.039) | 184 | 0 |
| Mean | 0.782 | 0.916 (+0.134) | 422 total | 0 |

The largest gains are on the clips that were worst before (14_6 rose from 0.477 to 0.906, 14_5 from 0.627
to 0.902). The clips that were already good stayed good, so nothing regressed.

## How we got these results

1. Better cross-camera matching. The cameras that face each other from opposite sides of the pitch used
 to split one player into two separate identities. We corrected how strongly a confident same-ground-
 position match is trusted, so those splits now merge back into one person. This is the main reason
 agreement went up, and why the previously worst clips improved the most.

2. A physical speed check on the output. Player markers used to jump across the field and back in a single
 frame, which is physically impossible. We now drop any frame in which a marker would have to move
 faster than a person can run. The visible teleports are gone.

3. Removing ghost detections. A single camera sometimes sees only a head, or half of a body cut off at the
 frame edge, and the system used to turn that into a phantom extra player. We now drop those partial
 single-camera detections, which moves the identity count closer to the true roster.

4. A rebuilt 3D reconstruction. The 3D step was consolidated into one clean stage using a fuller skeleton
 that includes the feet, which gives more reliable ground positions.

5. A final physics pass (new this cycle). After identity is decided, a new stage makes each 3D skeleton
 physically valid: constant bone lengths, no backward-bending knees or elbows, and steadier hips. This
 fixes the jitter, wobble, and impossible-limb issues raised last time.

Note on honesty: the hip-to-ground projection and the robust-triangulation experiments were also done, but
they did not change the numbers, so they are kept as options rather than defaults. The measured gains above
came from items 1, 2, and 5.

Sources: V8.0 from the V8.0 benchmark run; Current from the per-delivery identity metrics on the same 8
deliveries. No values are estimated.
