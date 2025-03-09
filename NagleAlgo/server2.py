#!/usr/bin/env python3
import argparse
import socket
import time
import sys
import struct
import subprocess

# TCP_QUICKACK is Linux-specific; if not defined in socket, define it.
if not hasattr(socket, "TCP_QUICKACK"):
    socket.TCP_QUICKACK = 12  # typical value on Linux

def set_loopback_delay(ms=50):
    """
    Inject an artificial delay on the loopback interface using tc/netem.
    Requires sudo privileges.
    """
    try:
        subprocess.run([
            "sudo", "tc", "qdisc", "add", "dev", "lo", "root", "netem",
            f"delay", f"{ms}ms"
        ], check=True)
        print(f"[INFO] Added {ms} ms delay to loopback interface.")
    except subprocess.CalledProcessError as e:
        print("[WARN] Could not add netem delay on lo (maybe it's already set?):", e)

def clear_loopback_delay():
    """
    Remove any existing netem qdisc on the loopback interface.
    """
    try:
        subprocess.run([
            "sudo", "tc", "qdisc", "del", "dev", "lo", "root", "netem"
        ], check=True)
        print("[INFO] Removed netem delay from loopback interface.")
    except subprocess.CalledProcessError as e:
        print("[WARN] Could not remove netem delay (maybe none was set?):", e)

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
            # 8 bytes header + 21 integers (84 bytes)
            _header = struct.unpack("B" * 8, tcp_info[:8])
            ints = struct.unpack("I" * 21, tcp_info[8:])
            total_retrans = ints[-1]
            return total_retrans
        elif len(tcp_info) == 104:
            # 8 bytes header + 24 integers (96 bytes)
            _header = struct.unpack("B" * 8, tcp_info[:8])
            ints = struct.unpack("I" * 24, tcp_info[8:])
            total_retrans = ints[-1]
            return total_retrans
        else:
            print("Unexpected TCP_INFO length:", len(tcp_info))
            return None
    except Exception as e:
        print("Could not get TCP_INFO:", e)
        return None

def run_server(bind_ip, bind_port, delayed_ack_enabled, add_delay):
    # If requested, add artificial delay to loopback
    if bind_ip == "127.0.0.1" and add_delay:
        set_loopback_delay(50)  # 50 ms delay on loopback

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
    duration = 130  # run ~2 minutes to capture data
    tcp_info_before = get_tcp_info(conn)
    
    conn.settimeout(5)
    try:
        while time.time() - start_time < duration:
            try:
                data = conn.recv(1024)
                if not data:
                    break
                chunk_len = len(data)
                total_bytes += chunk_len
                if chunk_len > max_chunk:
                    max_chunk = chunk_len
            except socket.timeout:
                break
    except KeyboardInterrupt:
        pass
    
    end_time = time.time()
    elapsed = end_time - start_time
    throughput = total_bytes / elapsed if elapsed > 0 else 0
    # We expect only 4KB of real data from the client
    goodput = 4096 / elapsed if elapsed > 0 else 0
    
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
    print(f"Approx. retransmissions (proxy for packet loss): {retransmissions}")
    print(f"Max chunk size in one recv(): {max_chunk} bytes")
    
    conn.close()
    s.close()

    # Clean up any artificial delay we added
    if bind_ip == "127.0.0.1" and add_delay:
        clear_loopback_delay()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="TCP Server for Nagle/Delayed-ACK experiment (with optional loopback delay)"
    )
    parser.add_argument("--bind_ip", type=str, default="0.0.0.0",
                        help="IP address to bind to (use 127.0.0.1 if you want loopback delay)")
    parser.add_argument("--port", type=int, default=5001, help="Port to listen on")
    parser.add_argument("--delayed_ack", choices=["on", "off"], default="on",
                        help="Enable or disable delayed ACK on the server side")
    parser.add_argument("--add_delay", action="store_true",
                        help="If set, adds 50 ms netem delay on loopback (requires sudo).")
    args = parser.parse_args()
    
    delayed_ack_enabled = (args.delayed_ack == "on")
    run_server(args.bind_ip, args.port, delayed_ack_enabled, args.add_delay)
