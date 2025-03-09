#include <iostream>
#include <string>
#include <sstream>
#include <vector>
#include <algorithm>
#include <cstring>
#include <cctype>
#include <stdexcept>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>

// Process the client task given in the format "choice:data"
std::string processTask(const std::string& task) {
    try {
        size_t pos = task.find(":");
        if (pos == std::string::npos) {
            return "Error processing task: Invalid task format";
        }
        std::string choiceStr = task.substr(0, pos);
        std::string data = task.substr(pos + 1);
        int choice = std::stoi(choiceStr);

        switch(choice) {
            case 1: {
                // Swap the case of each letter in the string
                for (char& c : data) {
                    if (std::islower(c))
                        c = std::toupper(c);
                    else if (std::isupper(c))
                        c = std::tolower(c);
                }
                return data;
            }
            case 2: {
                // Reverse the string
                std::string reversed = data;
                std::reverse(reversed.begin(), reversed.end());
                return reversed;
            }
            case 3:
                return "Goodbye!";
            default:
                return "Invalid choice.";
        }
    } catch (const std::exception& e) {
        return std::string("Error processing task: ") + e.what();
    }
}

int main() {
    const char* HOST = "192.168.64.3";
    const int PORT = 8080;

    // Create a TCP socket
    int serverSocket = socket(AF_INET, SOCK_STREAM, 0);
    if (serverSocket < 0) {
        std::cerr << "Error: Could not create socket.\n";
        return 1;
    }

    // Setup server address structure
    sockaddr_in serverAddr;
    std::memset(&serverAddr, 0, sizeof(serverAddr));
    serverAddr.sin_family = AF_INET;
    serverAddr.sin_port = htons(PORT);
    if (inet_pton(AF_INET, HOST, &serverAddr.sin_addr) <= 0) {
        std::cerr << "Error: Invalid address/Address not supported.\n";
        close(serverSocket);
        return 1;
    }

    // Bind the socket to the specified IP and port
    if (bind(serverSocket, reinterpret_cast<sockaddr*>(&serverAddr), sizeof(serverAddr)) < 0) {
        std::cerr << "Error: Bind failed.\n";
        close(serverSocket);
        return 1;
    }

    // Listen for incoming connections (backlog set to 100)
    if (listen(serverSocket, 100) < 0) {
        std::cerr << "Error: Listen failed.\n";
        close(serverSocket);
        return 1;
    }

    std::cout << "Server is running on " << HOST << ":" << PORT << "...\n";

    // Main server loop to accept client connections
    while (true) {
        std::cout << "Waiting for a client to connect...\n";
        sockaddr_in clientAddr;
        socklen_t clientLen = sizeof(clientAddr);
        int clientSocket = accept(serverSocket, reinterpret_cast<sockaddr*>(&clientAddr), &clientLen);
        if (clientSocket < 0) {
            std::cerr << "Error: Accept failed.\n";
            continue;
        }

        char clientIP[INET_ADDRSTRLEN];
        inet_ntop(AF_INET, &clientAddr.sin_addr, clientIP, INET_ADDRSTRLEN);
        std::cout << "TCP connection established with " << clientIP << ":" 
                  << ntohs(clientAddr.sin_port) << "\n";

        // Process client tasks until the client disconnects or sends the exit command
        while (true) {
            char buffer[1024] = {0};
            ssize_t bytesReceived = recv(clientSocket, buffer, sizeof(buffer) - 1, 0);
            if (bytesReceived <= 0) {
                std::cout << "Client " << clientIP << " disconnected.\n";
                break;
            }

            std::string data(buffer, bytesReceived);
            std::cout << "Received task from " << clientIP << ": " << data << "\n";
            std::string response = processTask(data);

            send(clientSocket, response.c_str(), response.size(), 0);

            if (response == "Goodbye!") {
                std::cout << "Closing connection with " << clientIP << "\n";
                break;
            }
        }
        close(clientSocket);
    }

    close(serverSocket);
    return 0;
}
