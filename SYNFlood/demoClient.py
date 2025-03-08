import socket

def display_menu():
    print("\nMenu:")
    print("1. Change the case of a string")
    print("2. Evaluate a mathematical expression")
    print("3. Find the reverse of a string")
    print("4. Exit")

def main():
    HOST = "192.168.64.3"
    PORT = 8080

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((HOST, PORT))
            while True:
                display_menu()
                
                choice = input("Enter your choice (1-4): ").strip()
                if choice not in {"1", "2", "3", "4"}:
                    print("Invalid choice. Please enter a number between 1 and 4.")
                    continue

                if choice == "4":
                    s.sendall(f"{choice}:".encode())
                    print("Exiting...")
                    break

                data = input("Enter input: ").strip()
                task = f"{choice}:{data}"

                s.sendall(task.encode())

                response = s.recv(1024).decode()
                print(f"Server response: {response}")

        except ConnectionRefusedError:
            print("Failed to connect to the server. Ensure it's running.")
        except KeyboardInterrupt:
            print("\nClient exiting...")

if __name__ == "__main__":
    main()
