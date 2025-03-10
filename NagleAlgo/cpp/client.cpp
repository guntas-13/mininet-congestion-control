// client.cpp
#include <iostream>
#include <thread>
#include <chrono>
#include <fstream>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <errno.h>
#include <string.h>
#include <netinet/tcp.h>

using namespace std;

const char* SERVER_IP = "192.168.64.3";
const int SERVER_PORT = 8080;
const char* CLIENT_IP = "192.168.64.2";
const int CHUNK_SIZE = 40; // 40 bytes/sec
const int TOTAL_DURATION = 120; // ~2 minutes

void set_socket_options(int sock, bool nagle_enabled, bool delayed_ack_enabled) {
    int opt;

    // Nagle's Algorithm
    opt = nagle_enabled ? 0 : 1; // 0=enable, 1=disable
    if (setsockopt(sock, IPPROTO_TCP, TCP_NODELAY, &opt, sizeof(opt)) < 0) {
        cerr << "Failed to set TCP_NODELAY: " << strerror(errno) << endl;
    }

    // Delayed-ACK
    opt = delayed_ack_enabled ? 0 : 1; // 0=enable, 1=disable
    if (setsockopt(sock, IPPROTO_TCP, TCP_QUICKACK, &opt, sizeof(opt)) < 0) {
        cerr << "Failed to set TCP_QUICKACK: " << strerror(errno) << endl;
    }
}

void transmit_file(bool nagle_enabled, bool delayed_ack_enabled) {
    int sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock < 0) {
        cerr << "Socket creation failed: " << strerror(errno) << endl;
        return;
    }

    // Bind to client IP
    sockaddr_in client_addr;
    client_addr.sin_family = AF_INET;
    client_addr.sin_port = 0;
    inet_pton(AF_INET, CLIENT_IP, &client_addr.sin_addr);
    if (bind(sock, (struct sockaddr*)&client_addr, sizeof(client_addr)) < 0) {
        cerr << "Bind failed: " << strerror(errno) << endl;
        close(sock);
        return;
    }

    // Set socket options
    set_socket_options(sock, nagle_enabled, delayed_ack_enabled);

    // Connect to server
    sockaddr_in server_addr;
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(SERVER_PORT);
    inet_pton(AF_INET, SERVER_IP, &server_addr.sin_addr);

    if (connect(sock, (struct sockaddr*)&server_addr, sizeof(server_addr)) < 0) {
        cerr << "Connect failed: " << strerror(errno) << endl;
        close(sock);
        return;
    }

    // Read 4KB file
    ifstream file("input.txt", ios::binary);
    if (!file) {
        cerr << "Failed to open input file" << endl;
        close(sock);
        return;
    }

    char buffer[CHUNK_SIZE];
    size_t total_sent = 0;
    time_t start_time = time(nullptr);

    cout << "Starting transmission at " << start_time << endl;

    while (total_sent < 4096 && (time(nullptr) - start_time) < TOTAL_DURATION) {
        file.read(buffer, CHUNK_SIZE);
        size_t to_send = min(static_cast<size_t>(CHUNK_SIZE), static_cast<size_t>(4096 - total_sent));
        ssize_t sent = send(sock, buffer, to_send, 0);
        if (sent < 0) {
            cerr << "Send failed: " << strerror(errno) << endl;
            break;
        }
        total_sent += sent;
        cout << "Sent " << sent << " bytes, total " << total_sent << " at " << time(nullptr) << endl;
        this_thread::sleep_for(chrono::microseconds(500)); // 40bytes per 0.5 ms
    }

    file.close();
    close(sock);
    cout << "Transmission complete, total sent: " << total_sent << " bytes" << endl;
}

int main(int argc, char* argv[]) {
    if (argc != 3) {
        cerr << "Usage: " << argv[0] << " <nagle_enabled: 0/1> <delayed_ack_enabled: 0/1>" << endl;
        return 1;
    }

    bool nagle_enabled = atoi(argv[1]) == 1;
    bool delayed_ack_enabled = atoi(argv[2]) == 1;

    cout << "Client: Nagle=" << (nagle_enabled ? "enabled" : "disabled")
         << ", Delayed-ACK=" << (delayed_ack_enabled ? "enabled" : "disabled") << endl;

    transmit_file(nagle_enabled, delayed_ack_enabled);
    return 0;
}
