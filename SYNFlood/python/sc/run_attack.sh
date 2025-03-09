#!/bin/bash

# Ensure Python scripts are executable
chmod +x legitimate.py syn_flood.py

# Start legitimate traffic at t=0s in background
echo "t=0s: Starting legitimate traffic"
python3 legitimate.py > legitimate.log 2>&1 &
LEGIT_PID=$!

# Wait 20 seconds
sleep 20

# Start SYN flood at t=20s in background
echo "t=20s: Starting SYN flood attack"
sudo python3 syn_flood.py > syn_flood.log 2>&1 &
FLOOD_PID=$!

# Wait 80 seconds (until t=100s)
sleep 80

# Stop SYN flood at t=100s
echo "t=100s: Stopping SYN flood attack"
sudo kill $FLOOD_PID

# Wait 40 seconds (until t=140s)
sleep 40

# Stop legitimate traffic at t=140s
echo "t=140s: Stopping legitimate traffic"
kill $LEGIT_PID

echo "Demonstration complete"