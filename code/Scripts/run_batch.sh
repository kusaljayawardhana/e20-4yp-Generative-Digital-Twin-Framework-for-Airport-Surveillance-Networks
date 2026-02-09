#!/bin/bash

# 1. Move to ns-3 directory
cd /home/e20179/ns-3-dev

# 2. Define Directories
BASE_DIR="scratch/airport-digital-twin"
INPUT_DIR="$BASE_DIR/final_scenarios_core" 
OUTPUT_DIR="$BASE_DIR/output"

# 3. EXACT OPTIMIZED BINARY PATH (From your build log)
BINARY="./build/scratch/airport-digital-twin/ns3.46-airport_digital_twin-optimized"

# Safety Check
if [ ! -f "$BINARY" ]; then
    echo "ERROR: Could not find binary at $BINARY"
    exit 1
fi

mkdir -p $OUTPUT_DIR

# 4. The Fast Loop
for i in {0000..0999}
do
    echo "Running Simulation $i..."
    $BINARY --scenario=$INPUT_DIR/scenario_$i.json --output=$OUTPUT_DIR/results_$i.json
done

echo "Done!"