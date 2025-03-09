#!/usr/bin/env python3
import argparse
import socket
import time
import sys
import struct

# TCP_QUICKACK is Linux-specific; if not defined in socket, define it.
if not hasattr(socket, "TCP_QUICKACK"):
    socket.TCP_QUICKACK = 12  # typical value on Linux

def get_tcp_info(sock):
    """
    Retrieve TCP_INFO from the socket and extract tcpi_total_retrans.
    The structure size may be 92 or 104 bytes depending on your system.
    """
    try:
        # Request a buffer size that works for most systems.
        bufsize = 104
        tcp_info = sock.getsockopt(socket.IPPROTO_TCP, socket.TCP_INFO, bufsize)
        if len(tcp_info) == 92:
            # For 92 bytes: 8 bytes header + 21 integers (84 bytes)
            header = struct.unpack("B" * 8, tcp_info[:8])
            ints = struct.unpack("I" * 21, tcp_info[8:])
            total_retrans = ints[-1]
            return total_retrans
        elif len(tcp_info) == 104:
            # For 104 bytes: 8 bytes header + 24 integers (96 bytes)
            header = struct.unpack("B" * 8, tcp_info[:8])
            ints = struct.unpack("I" * 24, tcp_info[8:])
            total_retrans = ints[-1]
            return total_retrans
        else:
            print("Unexpected TCP_INFO length:", len(tcp_info))
            return None
    except Exception as e:
        print("Could not get TCP_INFO:", e)
        return None

def run_server(bind_ip, bind_port, delayed_ack_enabled):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((bind_ip, bind_port))
    s.listen(1)
    print(f"Server listening on {bind_ip}:{bind_port}")
    
    conn, addr = s.accept()
    print("Connection from", addr)
    
    # If delayed ACK is disabled, try to set TCP_QUICKACK on the accepted socket.
    if not delayed_ack_enabled:
        try:
            conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_QUICKACK, 1)
            print("Delayed ACK disabled (TCP_QUICKACK set)")
        except Exception as e:
            print("Failed to disable delayed ACK:", e)
    
    total_bytes = 0
    max_chunk = 0
    start_time = time.time()
    duration = 130  # run a bit longer than 2 minutes to capture all data
    tcp_info_before = get_tcp_info(conn)
    
    # Set a small timeout so that recv() does not block indefinitely.
    conn.settimeout(5)
    try:
        while time.time() - start_time < duration:
            try:
                # Using a modest buffer size (say 1024) to try to capture individual segments.
                data = conn.recv(1024)
                if not data:
                    break
                chunk_len = len(data)
                total_bytes += chunk_len
                if chunk_len > max_chunk:
                    max_chunk = chunk_len
            except socket.timeout:
                # If no data is received within timeout, break
                break
    except KeyboardInterrupt:
        pass
    
    end_time = time.time()
    elapsed = end_time - start_time
    throughput = total_bytes / elapsed  # bytes per second
    goodput = 4096 / elapsed  # since only 4 KB of payload should be delivered
    
    tcp_info_after = get_tcp_info(conn)
    if tcp_info_before is not None and tcp_info_after is not None:
        retransmissions = tcp_info_after - tcp_info_before
    else:
        retransmissions = "N/A"
    
    print("=== Performance Metrics ===")
    print(f"Elapsed time: {elapsed:.2f} seconds")
    print(f"Total bytes received: {total_bytes}")
    print(f"Throughput: {throughput:.2f} bytes/sec")
    print(f"Goodput (application data): {goodput:.2f} bytes/sec")
    print(f"Approximate retransmissions (proxy for packet loss): {retransmissions}")
    print(f"Maximum chunk size received in one call: {max_chunk} bytes")
    
    conn.close()
    s.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TCP Server for Nagle/Delayed-ACK experiment")
    parser.add_argument("--bind_ip", type=str, default="0.0.0.0", help="IP address to bind to")
    parser.add_argument("--port", type=int, default=5001, help="Port to listen on")
    parser.add_argument("--delayed_ack", choices=["on", "off"], default="on", help="Enable or disable delayed ACK")
    args = parser.parse_args()
    
    delayed_ack_enabled = (args.delayed_ack == "on")
    run_server(args.bind_ip, args.port, delayed_ack_enabled)
