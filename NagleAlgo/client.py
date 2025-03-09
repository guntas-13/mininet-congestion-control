#!/usr/bin/env python3
import argparse
import socket
import time
import sys

# TCP_NODELAY is used to disable Nagle’s algorithm.
def run_client(server_ip, server_port, nagle_enabled, delayed_ack_enabled):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # If Nagle's algorithm is disabled, set TCP_NODELAY.
    if not nagle_enabled:
        try:
            s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            print("Nagle's algorithm disabled (TCP_NODELAY set)")
        except Exception as e:
            print("Failed to disable Nagle's algorithm:", e)
    
    # For delayed ACK on client side: if disabling delayed ACK,
    # try to set TCP_QUICKACK. (Note: This is Linux-specific.)
    if not delayed_ack_enabled:
        try:
            if hasattr(socket, "TCP_QUICKACK"):
                s.setsockopt(socket.IPPROTO_TCP, socket.TCP_QUICKACK, 1)
                print("Client delayed ACK disabled (TCP_QUICKACK set)")
            else:
                print("TCP_QUICKACK not available on this system.")
        except Exception as e:
            print("Failed to disable delayed ACK on client:", e)
    
    try:
        s.connect((server_ip, server_port))
    except Exception as e:
        print("Connection error:", e)
        sys.exit(1)
    
    # Generate a 4KB data block to send (for example purposes).
    file_size = 4096  # bytes
    data = b'A' * file_size  # 4KB of data
    chunk_size = 40     # bytes per transmission (to achieve ~40 bytes/sec)
    
    print(f"Starting transmission of 4KB file in {chunk_size}-byte chunks.")
    sent_bytes = 0
    start_time = time.time()
    
    # Send the file in 40-byte chunks with 1 second delay between sends.
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i+chunk_size]
        try:
            s.sendall(chunk)
            sent_bytes += len(chunk)
            print(f"Sent chunk {i//chunk_size+1}: {len(chunk)} bytes (Total sent: {sent_bytes} bytes)")
        except Exception as e:
            print("Send error:", e)
            break
        time.sleep(0.01)  # wait 10 milli second between chunks
    
    end_time = time.time()
    elapsed = end_time - start_time
    print("=== Transmission complete ===")
    print(f"Elapsed time: {elapsed:.2f} seconds")
    print(f"Total bytes sent: {sent_bytes}")
    
    s.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TCP Client for Nagle/Delayed-ACK experiment")
    parser.add_argument("--server_ip", type=str, default="127.0.0.1", help="Server IP address")
    parser.add_argument("--port", type=int, default=5001, help="Server port")
    parser.add_argument("--nagle", choices=["on", "off"], default="on", help="Enable or disable Nagle's algorithm")
    parser.add_argument("--delayed_ack", choices=["on", "off"], default="on", help="Enable or disable delayed ACK")
    args = parser.parse_args()
    
    nagle_enabled = (args.nagle == "on")
    delayed_ack_enabled = (args.delayed_ack == "on")
    run_client(args.server_ip, args.port, nagle_enabled, delayed_ack_enabled)
