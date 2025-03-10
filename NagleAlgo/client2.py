#!/usr/bin/env python3
import argparse
import socket
import subprocess
import time
import os

def set_delayed_ack(enabled):
    """
    Adjust the kernel’s delayed ACK timers on the client side.
    For older kernels, use tcp_delack_min/max;
    for newer kernels, use tcp_delack_ticks.
    """
    param_min = "/proc/sys/net/ipv4/tcp_delack_min"
    param_max = "/proc/sys/net/ipv4/tcp_delack_max"
    param_ticks = "/proc/sys/net/ipv4/tcp_delack_ticks"

    if os.path.exists(param_min) and os.path.exists(param_max):
        if enabled:
            print("Setting Delayed ACK timers (tcp_delack_min/max) to defaults (enabled).")
            subprocess.run(["sudo", "sysctl", "-w", "net.ipv4.tcp_delack_min=40"], check=True)
            subprocess.run(["sudo", "sysctl", "-w", "net.ipv4.tcp_delack_max=200"], check=True)
        else:
            print("Disabling Delayed ACK (tcp_delack_min/max set to 0).")
            subprocess.run(["sudo", "sysctl", "-w", "net.ipv4.tcp_delack_min=0"], check=True)
            subprocess.run(["sudo", "sysctl", "-w", "net.ipv4.tcp_delack_max=0"], check=True)
    elif os.path.exists(param_ticks):
        if enabled:
            print("Setting Delayed ACK using tcp_delack_ticks to 5 (enabled).")
            subprocess.run(["sudo", "sysctl", "-w", "net.ipv4.tcp_delack_ticks=5"], check=True)
        else:
            print("Disabling Delayed ACK by setting tcp_delack_ticks to 1.")
            subprocess.run(["sudo", "sysctl", "-w", "net.ipv4.tcp_delack_ticks=1"], check=True)
    else:
        print("Warning: No Delayed ACK sysctl parameters found. Skipping configuration.")

def run_client(server_ip, port, nagle_enabled, delayed_ack_enabled):
    # Configure delayed ACK on the client side
    set_delayed_ack(delayed_ack_enabled)
    
    # Create a TCP socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Adjust Nagle's algorithm based on the provided setting
    if not nagle_enabled:
        print("Disabling Nagle's algorithm (setting TCP_NODELAY).")
        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    else:
        print("Nagle's algorithm enabled (default behavior).")
    
    s.connect((server_ip, port))
    print(f"Connected to server at {server_ip}:{port} with Nagle {'enabled' if nagle_enabled else 'disabled'} and Delayed ACK {'enabled' if delayed_ack_enabled else 'disabled'}.")
    
    # Create a 4 KB file (simulated by 4096 bytes of 'a')
    file_data = b'a' * 4096
    total_sent = 0
    start_time = time.time()
    
    # Send data in 40-byte chunks with 1-second intervals
    for i in range(0, len(file_data), 40):
        chunk = file_data[i:i+40]
        sent = s.send(chunk)
        total_sent += sent
        time.sleep(1)
    
    end_time = time.time()
    duration = end_time - start_time
    print(f"Sent {total_sent} bytes in {duration:.2f} seconds")
    s.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TCP Client for Nagle and Delayed ACK Experiment")
    parser.add_argument("--server_ip", default="127.0.0.1", help="Server IP address")
    parser.add_argument("--port", type=int, default=5000, help="Server port number")
    parser.add_argument("--nagle", choices=["enabled", "disabled"], default="enabled", help="Enable or disable Nagle's algorithm")
    parser.add_argument("--delayedack", choices=["enabled", "disabled"], default="enabled", help="Enable or disable Delayed ACK")
    args = parser.parse_args()
    
    nagle_enabled = (args.nagle == "enabled")
    delayed_ack_enabled = (args.delayedack == "enabled")
    run_client(args.server_ip, args.port, nagle_enabled, delayed_ack_enabled)
