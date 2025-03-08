import socket

def process_task(task):
    """Process the client's task safely."""
    try:
        choice, data = task.split(":", 1)
        choice = int(choice)

        if choice == 1:
            return data.swapcase()
        elif choice == 2:
            return str(eval(data))    # Vulnerability here but will se
        elif choice == 3:
            return data[::-1]
        elif choice == 4:  # Exit
            return "Goodbye!"
        else:
            return "Invalid choice."
    except Exception as e:
        return f"Error processing task: {e}"

def main():
    HOST = "192.168.64.3"
    PORT = 8080

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(100)

    print(f"Server is running on {HOST}:{PORT}...")

    try:
        while True:
            print("Waiting for a client to connect...")
            conn, addr = server_socket.accept()
            print(f"TCP connection established with {addr}")

            while True:
                try:
                    data = conn.recv(1024).decode()
                    if not data:
                        print(f"Client {addr} disconnected.")
                        break

                    print(f"Received task from {addr}: {data}")
                    response = process_task(data)

                    conn.sendall(response.encode())

                    if response == "Goodbye!":
                        print(f"Closing connection with {addr}")
                        break

                except Exception as e:
                    print(f"Error handling client {addr}: {e}")
                    break

            conn.close()

    except KeyboardInterrupt:
        print("\nServer shutting down...")
    finally:
        server_socket.close()

if __name__ == "__main__":
    main()
