#!/bin/bash

# Compile the C++ programs
g++ legitimate.cpp -o legitimate
if [ $? -ne 0 ]; then
    echo "Compilation of legitimate.cpp failed"
    exit 1
fi

g++ syn_flood.cpp -o syn_flood
if [ $? -ne 0 ]; then
    echo "Compilation of syn_flood.cpp failed"
    exit 1
fi

# Start legitimate traffic at t=0s in background
echo "t=0s: Starting legitimate traffic"
./legitimate&
LEGIT_PID=$!

# Wait 20 seconds
sleep 20

# Start SYN flood at t=20s in background
echo "t=20s: Starting SYN flood attack"
sudo ./syn_flood &
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
