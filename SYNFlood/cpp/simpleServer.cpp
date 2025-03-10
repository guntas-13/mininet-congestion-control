// server.cpp
#include <iostream>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <unistd.h>

using namespace std;

int main() {
    const char* HOST = "192.168.64.3";
    const int PORT = 8080;

    int server_socket = socket(AF_INET, SOCK_STREAM, 0);
    if (server_socket == -1) {
        cerr << "Failed to create socket" << endl;
        return 1;
    }

    sockaddr_in server_addr;
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(PORT);
    server_addr.sin_addr.s_addr = inet_addr(HOST);

    if (bind(server_socket, (struct sockaddr*)&server_addr, sizeof(server_addr)) < 0) {
        cerr << "Bind failed" << endl;
        close(server_socket);
        return 1;
    }

    if (listen(server_socket, 256) < 0) {
        cerr << "Listen failed" << endl;
        close(server_socket);
        return 1;
    }

    cout << "Server running on " << HOST << ":" << PORT << "..." << endl;

    while (true) {
        sockaddr_in client_addr;
        socklen_t client_len = sizeof(client_addr);
        int client_socket = accept(server_socket, (struct sockaddr*)&client_addr, &client_len);

        if (client_socket < 0) {
            cerr << "Accept failed" << endl;
            continue;
        }

        char client_ip[INET_ADDRSTRLEN];
        inet_ntop(AF_INET, &(client_addr.sin_addr), client_ip, INET_ADDRSTRLEN);
        cout << "Connection from " << client_ip << ":" << ntohs(client_addr.sin_port) << endl;

        close(client_socket); // Immediately close to keep it simple
    }

    close(server_socket);
    return 0;
}
