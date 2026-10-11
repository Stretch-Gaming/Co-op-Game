#!/bin/bash
# Build and run the native Mac package; all options go to package_game.py.
exec python3 "$(dirname "$0")/package_game.py" "$@"
