import socket
import time

SERVER_IP = "192.168.64.3"
SERVER_PORT = 8080
CLIENT_IP = "192.168.64.2"

def legitimate_traffic():
    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.bind((CLIENT_IP, 0))
            sock.connect((SERVER_IP, SERVER_PORT))
            print(f"Legitimate connection established at {time.time()}")
            time.sleep(1)
            sock.close()
        except socket.error as e:
            print(f"Legitimate connection failed: {e} at {time.time()}")
        time.sleep(0.5)

if __name__ == "__main__":
    print("Starting legitimate traffic...")
    legitimate_traffic()