#!/bin/bash

# Compile the C++ programs
g++ -std=c++17 legitimate.cpp -o legitimate
if [ $? -ne 0 ]; then
    echo "Compilation of legitimate.cpp failed"
    exit 1
fi

g++ -std=c++17 syn_flood.cpp -o syn_flood
if [ $? -ne 0 ]; then
    echo "Compilation of syn_flood.cpp failed"
    exit 1
fi

# Start legitimate traffic at t=0s in background
echo "t=0s: Starting legitimate traffic"
./legitimate &
LEGIT_PID=$!

sleep 20

echo "t=20s: Starting SYN flood attack"
sudo ./syn_flood &
FLOOD_PID=$!

sleep 100

echo "t=120s: Stopping SYN flood attack"
sudo kill $FLOOD_PID

sleep 20

echo "t=140s: Stopping legitimate traffic"
kill $LEGIT_PID

echo "Demonstration complete"
