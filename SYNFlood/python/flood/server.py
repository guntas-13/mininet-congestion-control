import socket
import time

SERVER_IP = "192.168.64.3"
SERVER_PORT = 8080

def run_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((SERVER_IP, SERVER_PORT))
        server_socket.listen(1)
        print(f"Server listening on {SERVER_IP}:{SERVER_PORT}...")

        while True:
            try:
                client_socket, client_address = server_socket.accept()
                with client_socket:
                    print(f"Connection from {client_address} at {time.time()}")
                    time.sleep(1)
                    print(f"Closed connection from {client_address} at {time.time()}")
            except KeyboardInterrupt:
                print("Server shutting down...")
                break

if __name__ == "__main__":
    run_server()
