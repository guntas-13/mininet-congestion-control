// server.cpp
#include <iostream>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <errno.h>
#include <string.h>
#include <netinet/tcp.h>

using namespace std;

const char* SERVER_IP = "192.168.64.3";
const int SERVER_PORT = 8080;

void set_socket_options(int sock, bool nagle_enabled, bool delayed_ack_enabled) {
    int opt;

    // Nagle's Algorithm
    opt = nagle_enabled ? 0 : 1;
    if (setsockopt(sock, IPPROTO_TCP, TCP_NODELAY, &opt, sizeof(opt)) < 0) {
        cerr << "Failed to set TCP_NODELAY: " << strerror(errno) << endl;
    }

    // Delayed-ACK
    opt = delayed_ack_enabled ? 0 : 1;
    if (setsockopt(sock, IPPROTO_TCP, TCP_QUICKACK, &opt, sizeof(opt)) < 0) {
        cerr << "Failed to set TCP_QUICKACK: " << strerror(errno) << endl;
    }
}

void receive_file(int client_socket, bool nagle_enabled, bool delayed_ack_enabled) {
    set_socket_options(client_socket, nagle_enabled, delayed_ack_enabled);

    char buffer[4096];
    size_t total_received = 0;

    while (total_received < 4096) {
        ssize_t received = recv(client_socket, buffer, sizeof(buffer), 0);
        if (received <= 0) {
            if (received == 0) {
                cout << "Client closed connection" << endl;
            } else {
                cerr << "Recv failed: " << strerror(errno) << endl;
            }
            break;
        }
        total_received += received;
        cout << "Received " << received << " bytes, total " << total_received << " at " << time(nullptr) << endl;
    }

    cout << "Reception complete, total received: " << total_received << " bytes" << endl;
}

void run_server(bool nagle_enabled, bool delayed_ack_enabled) {
    int server_socket = socket(AF_INET, SOCK_STREAM, 0);
    if (server_socket < 0) {
        cerr << "Socket creation failed: " << strerror(errno) << endl;
        return;
    }

    int opt = 1;
    if (setsockopt(server_socket, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt)) < 0) {
        cerr << "Setsockopt failed: " << strerror(errno) << endl;
        close(server_socket);
        return;
    }

    sockaddr_in server_addr;
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(SERVER_PORT);
    inet_pton(AF_INET, SERVER_IP, &server_addr.sin_addr);

    if (bind(server_socket, (struct sockaddr*)&server_addr, sizeof(server_addr)) < 0) {
        cerr << "Bind failed: " << strerror(errno) << endl;
        close(server_socket);
        return;
    }

    if (listen(server_socket, 1) < 0) {
        cerr << "Listen failed: " << strerror(errno) << endl;
        close(server_socket);
        return;
    }

    cout << "Server listening on " << SERVER_IP << ":" << SERVER_PORT << endl;

    sockaddr_in client_addr;
    socklen_t client_len = sizeof(client_addr);
    int client_socket = accept(server_socket, (struct sockaddr*)&client_addr, &client_len);
    if (client_socket < 0) {
        cerr << "Accept failed: " << strerror(errno) << endl;
        close(server_socket);
        return;
    }

    char client_ip[INET_ADDRSTRLEN];
    inet_ntop(AF_INET, &client_addr.sin_addr, client_ip, INET_ADDRSTRLEN);
    cout << "Connection from " << client_ip << ":" << ntohs(client_addr.sin_port) << endl;

    receive_file(client_socket, nagle_enabled, delayed_ack_enabled);

    close(client_socket);
    close(server_socket);
}

int main(int argc, char* argv[]) {
    if (argc != 3) {
        cerr << "Usage: " << argv[0] << " <nagle_enabled: 0/1> <delayed_ack_enabled: 0/1>" << endl;
        return 1;
    }

    bool nagle_enabled = atoi(argv[1]) == 1;
    bool delayed_ack_enabled = atoi(argv[2]) == 1;

    cout << "Server: Nagle=" << (nagle_enabled ? "enabled" : "disabled")
         << ", Delayed-ACK=" << (delayed_ack_enabled ? "enabled" : "disabled") << endl;

    run_server(nagle_enabled, delayed_ack_enabled);
    return 0;
}