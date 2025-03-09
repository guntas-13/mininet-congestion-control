#include <iostream>
#include <string>
#include <cstring>      // for memset
#include <sys/types.h>
#include <sys/socket.h>
#include <arpa/inet.h>  // for inet_pton
#include <unistd.h>     // for close

void displayMenu() {
    std::cout << "\nMenu:\n";
    std::cout << "1. Change the case of a string\n";
    std::cout << "2. Find the reverse of a string\n";
    std::cout << "3. Exit\n";
}

int main() {
    const char* HOST = "192.168.64.3";
    const int PORT = 8080;

    // Create socket
    int sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock < 0) {
        std::cerr << "Error: Could not create socket.\n";
        return 1;
    }

    // Setup server address structure
    sockaddr_in serverAddr;
    memset(&serverAddr, 0, sizeof(serverAddr));
    serverAddr.sin_family = AF_INET;
    serverAddr.sin_port = htons(PORT);
    if (inet_pton(AF_INET, HOST, &serverAddr.sin_addr) <= 0) {
        std::cerr << "Error: Invalid address/ Address not supported.\n";
        close(sock);
        return 1;
    }

    // Connect to server
    if (connect(sock, reinterpret_cast<sockaddr*>(&serverAddr), sizeof(serverAddr)) < 0) {
        std::cerr << "Failed to connect to the server. Ensure it's running.\n";
        close(sock);
        return 1;
    }

    std::string choice, inputData;
    while (true) {
        displayMenu();
        std::cout << "Enter your choice (1-3): ";
        std::getline(std::cin, choice);
        
        // Validate choice
        if (choice != "1" && choice != "2" && choice != "3") {
            std::cout << "Invalid choice. Please enter a number between 1 and 3.\n";
            continue;
        }

        // If exit option chosen
        if (choice == "3") {
            std::string exitMsg = choice + ":";
            send(sock, exitMsg.c_str(), exitMsg.size(), 0);
            std::cout << "Exiting...\n";
            break;
        }

        std::cout << "Enter input: ";
        std::getline(std::cin, inputData);
        std::string task = choice + ":" + inputData;
        
        // Send task to the server
        if (send(sock, task.c_str(), task.size(), 0) < 0) {
            std::cerr << "Failed to send data to server.\n";
            break;
        }

        // Receive response from the server
        char buffer[1024] = {0};
        ssize_t bytesReceived = recv(sock, buffer, sizeof(buffer) - 1, 0);
        if (bytesReceived <= 0) {
            std::cerr << "Failed to receive data or connection closed by server.\n";
            break;
        }
        std::cout << "Server response: " << buffer << "\n";
    }

    close(sock);
    return 0;
}
