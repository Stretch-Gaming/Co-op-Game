#!/bin/bash
# Host the six-round adventure; clients use Tools/join.command IP.
exec /bin/bash "$(dirname "$0")/launch_preview/launch.sh" host /Game/Puzzles/Test/SixRound/L_SixRound_Test "$@"
