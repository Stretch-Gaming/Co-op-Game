#!/bin/bash
# Usage: Tools/play-connected.command [--dry-run]
exec /bin/bash "$(dirname "$0")/launch_preview/launch.sh" preview "$@"
