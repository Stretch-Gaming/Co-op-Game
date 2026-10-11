# Environment quality checks

This pass adds read-only checks for the connected preview: visible-floor/capsule inspection, audio signal quality, and reproducible native performance collection. No game assets, puzzles, settings or audio hooks are changed.

- Geometry:74 native points all supported; one rock-edge overlap has a clear nearby sampled detour. No passage bug proved.
- Audio:9 source files show no clipping/DC/loop-seam warnings; aligned chase layers peak at-1.229dBFS. No listening or true-peak judgment is claimed.
- Performance:1015 actors,113 lights(37 shadow lights),5642 instances inventoried. Native room/maze timing now completed after GPU handback; shared-load editor limits remain. Counts and timings do not yet justify an optimization.

Read each folder README for tools, guards, evidence and remaining checks. The primary alone operates the editor. Other adventure work remains in its separate chat/checkouts.
