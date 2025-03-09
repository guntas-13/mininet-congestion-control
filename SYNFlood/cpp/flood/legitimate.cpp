// legitimate.cpp
#include <iostream>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <errno.h>
#include <string.h>

using namespace std;

const char* SERVER_IP = "192.168.64.3";
const int SERVER_PORT = 8080;
const char* CLIENT_IP = "192.168.64.2";

void legitimate_traffic() {
    while (true) {
        int sock = socket(AF_INET, SOCK_STREAM, 0);
        if (sock < 0) {
            cerr << "Socket creation failed: " << strerror(errno) << endl;
            usleep(500000); // 500ms delay
            continue;
        }

        sockaddr_in server_addr;
        server_addr.sin_family = AF_INET;
        server_addr.sin_port = htons(SERVER_PORT);
        inet_pton(AF_INET, SERVER_IP, &server_addr.sin_addr);

        if (connect(sock, (struct sockaddr*)&server_addr, sizeof(server_addr)) < 0) {
            cerr << "Legitimate connection failed: " << strerror(errno) << " at " << time(nullptr) << endl;
        } else {
            cout << "Legitimate connection established at " << time(nullptr) << endl;
            sleep(1); // Simulate work
        }
        close(sock);
        usleep(500000); // 500ms delay
    }
}

int main() {
    cout << "Starting legitimate traffic..." << endl;
    legitimate_traffic();
    return 0;
}