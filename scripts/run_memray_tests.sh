#!/bin/bash
# Script to run tests with memray memory profiling

set -e

echo "Running tests with memray memory profiling..."

# Create output directory
mkdir -p memory_profiles

# Run specific test with memray
echo "Profiling memory usage in collection operations..."
python -m memray run -o memory_profiles/test_collections.bin \
    -m pytest tests/test_memory_profiling.py::test_memory_efficient_string_building -v

# Generate flamegraph
echo "Generating flamegraph..."
python -m memray flamegraph memory_profiles/test_collections.bin \
    -o memory_profiles/test_collections_flamegraph.html

# Generate summary
echo -e "\nMemory usage summary:"
python -m memray summary memory_profiles/test_collections.bin

echo -e "\nMemory profiling complete!"
echo "View the flamegraph at: memory_profiles/test_collections_flamegraph.html"
