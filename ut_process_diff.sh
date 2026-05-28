#!/bin/bash
# Wrapper script for smart diff processing

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROCESSOR="$SCRIPT_DIR/ut_smart_diff_processor.py"

# Check if processor exists
if [ ! -f "$PROCESSOR" ]; then
    echo "Error: Smart diff processor not found at $PROCESSOR" >&2
    exit 1
fi

# Run the processor
python3 "$PROCESSOR" "$@"
