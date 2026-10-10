#!/bin/bash
# Usage: Tools/host.command [/Game/Maps/MapName] [--dry-run]
exec /bin/bash "$(dirname "$0")/launch_preview/launch.sh" host "$@"
