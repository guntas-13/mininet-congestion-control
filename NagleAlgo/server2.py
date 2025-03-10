#!/usr/bin/env python3
import argparse
import socket
import subprocess
import time
import os

def set_delayed_ack(enabled):
    """
    Adjust the kernel’s delayed ACK timers.
    For older kernels, use tcp_delack_min and tcp_delack_max;
    for newer kernels (e.g., on Ubuntu 24.04), use tcp_delack_ticks.
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
            # Assume the default ticks value is 5 (verify on your system)
            print("Setting Delayed ACK using tcp_delack_ticks to 5 (enabled).")
            subprocess.run(["sudo", "sysctl", "-w", "net.ipv4.tcp_delack_ticks=5"], check=True)
        else:
            # Setting to 1 to effectively reduce the delay
            print("Disabling Delayed ACK by setting tcp_delack_ticks to 1.")
            subprocess.run(["sudo", "sysctl", "-w", "net.ipv4.tcp_delack_ticks=1"], check=True)
    else:
        print("Warning: No Delayed ACK sysctl parameters found. Skipping configuration.")

def run_server(port, delayed_ack_enabled):
    # Configure delayed ACK on the server side
    set_delayed_ack(delayed_ack_enabled)
    
    # Create a TCP server socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('0.0.0.0', port))
    s.listen(1)
    print(f"Server listening on port {port} with Delayed ACK {'enabled' if delayed_ack_enabled else 'disabled'}.")

    conn, addr = s.accept()
    print("Accepted connection from", addr)
    
    total_received = 0
    start_time = time.time()
    # Continue receiving until 4096 bytes have been collected
    while total_received < 4096:
        data = conn.recv(1024)
        if not data:
            break
        total_received += len(data)
    
    end_time = time.time()
    duration = end_time - start_time
    throughput = total_received / duration
    print(f"Received {total_received} bytes in {duration:.2f} seconds")
    print(f"Throughput: {throughput:.2f} bytes/sec")
    
    conn.close()
    s.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TCP Server for Nagle and Delayed ACK Experiment")
    parser.add_argument("--port", type=int, default=5000, help="Port number to listen on")
    parser.add_argument("--delayedack", choices=["enabled", "disabled"], default="enabled", help="Enable or disable Delayed ACK")
    args = parser.parse_args()
    
    delayed_ack_enabled = (args.delayedack == "enabled")
    run_server(args.port, delayed_ack_enabled)
