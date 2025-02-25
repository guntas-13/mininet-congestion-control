#!/usr/bin/python3

"""
Mininet TCP Congestion Control Experiment Script

This script sets up a Mininet topology with 7 hosts (H1-H7) connected via 4 switches (S1-S4).
H7 runs an iperf3 TCP server and the other hosts are used as iperf3 TCP clients.
Traffic is generated using:
    iperf3 -c <server_ip> -p <server_port> -b 10M -P 10 -t <duration> -C <cc_scheme>

Experiments:
    a. Single client on H1.
    b. Staggered clients: H1 at T=0s (150s), H3 at T=15s (120s), H4 at T=30s (90s).
    c. Bandwidth-controlled experiments:
         c1. Only client H3.
         c2a. Clients H1 and H2.
         c2b. Clients H1 and H3.
         c2c. Clients H1, H3, and H4.
    d. Optionally, set link loss on the link S2-S3 (e.g., 1% or 5%) and repeat experiment (c).

Usage:
    sudo python3 script.py <option> <cc_scheme> [loss]

    <option>: a, b, c1, c2a, c2b, or c2c
    <cc_scheme>: TCP congestion control scheme (e.g., reno, cubic, bbr)
    [loss]: Optional. Packet loss percentage for link S2-S3 (default 0)
"""

import sys
import time
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Controller, OVSKernelSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info

class CustomTopo(Topo):
    def build(self, link_loss=0, bandwidths=None):
        """
        Builds the topology.
        :param link_loss: Packet loss percentage for the link between S2 and S3.
        :param bandwidths: Dictionary defining bandwidth for switch links.
                           Expected keys: 's1-s2', 's2-s3', 's3-s4'
        """
        if bandwidths is None:
            # Default bandwidths (in Mbps) as specified in part (c)
            bandwidths = {'s1-s2': 100, 's2-s3': 50, 's3-s4': 100}

        # Create switches
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        s3 = self.addSwitch('s3')
        s4 = self.addSwitch('s4')

        # Create hosts
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        h3 = self.addHost('h3')
        h4 = self.addHost('h4')
        h5 = self.addHost('h5')
        h6 = self.addHost('h6')
        h7 = self.addHost('h7')

        # Connect hosts to switches
        self.addLink(h1, s1)
        self.addLink(h2, s1)
        self.addLink(h3, s2)
        self.addLink(h4, s3)
        self.addLink(h5, s3)
        self.addLink(h6, s4)
        self.addLink(h7, s4)

        # Connect switches with given bandwidth and loss settings
        self.addLink(s1, s2, bw=bandwidths['s1-s2'])
        self.addLink(s2, s3, bw=bandwidths['s2-s3'], loss=link_loss)
        self.addLink(s3, s4, bw=bandwidths['s3-s4'])

def run_experiment(option, cc_scheme, link_loss=0):
    """
    Sets up the network, starts the iperf3 server, and runs clients based on the selected experiment option.
    :param option: Experiment option (a, b, c1, c2a, c2b, c2c)
    :param cc_scheme: TCP congestion control scheme (e.g., reno, cubic, bbr)
    :param link_loss: Packet loss percentage for link S2-S3.
    """
    setLogLevel('info')

    # Bandwidth configuration as specified for part (c)
    bandwidths = {'s1-s2': 100, 's2-s3': 50, 's3-s4': 100}

    # Create network with custom topology, applying loss if provided
    net = Mininet(topo=CustomTopo(link_loss=link_loss, bandwidths=bandwidths),
                  controller=Controller,
                  switch=OVSKernelSwitch,
                  autoSetMacs=True)
    info('*** Starting network\n')
    net.start()
    # Populate ARP tables and verify connectivity
    net.staticArp()
    net.pingAll()

    # Get hosts
    h1, h2, h3, h4, h5, h6, h7 = net.get('h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'h7')

    # Start the iperf3 server on H7 (running in background)
    info('*** Starting iperf3 server on H7\n')
    # h7.cmd('ifconfig > iperf3_server.txt')
    h7.cmd('iperf3 -s -p 5000 -D')
    time.sleep(2)

    info('*** Starting iperf3 client(s) with congestion control scheme: %s\n' % cc_scheme)
    if option == 'a':
        # Part (a): Run client on H1 for 150 seconds
        h1.cmd(f'iperf3 -c {h7.IP()} -p 5000 -b 10M -P 10 -t 150 -C {cc_scheme} --logfile temp.txt')

    elif option == 'b':
        # Part (b): Staggered clients: H1 at T=0, H3 at T=15, H4 at T=30
        h1.cmd(f'iperf3 -c {h7.IP()} -p 5000 -b 10M -P 10 -t 150 -C {cc_scheme} &')
        time.sleep(15)
        h3.cmd(f'iperf3 -c {h7.IP()} -p 5000 -b 10M -P 10 -t 120 -C {cc_scheme} &')
        time.sleep(15)
        h4.cmd(f'iperf3 -c {h7.IP()} -p 5000 -b 10M -P 10 -t 90 -C {cc_scheme} &')

    elif option == 'c1':
        # Part (c) condition 1: Only client on H3
        h3.cmd(f'iperf3 -c {h7.IP()} -p 5000 -b 10M -P 10 -t 150 -C {cc_scheme}')

    elif option == 'c2a':
        # Part (c) condition 2a: Clients on H1 and H2
        h1.cmd(f'iperf3 -c {h7.IP()} -p 5000 -b 10M -P 10 -t 150 -C {cc_scheme}')
        h2.cmd(f'iperf3 -c {h7.IP()} -p 5000 -b 10M -P 10 -t 150 -C {cc_scheme}')

    elif option == 'c2b':
        # Part (c) condition 2b: Clients on H1 and H3
        h1.cmd(f'iperf3 -c {h7.IP()} -p 5000 -b 10M -P 10 -t 150 -C {cc_scheme}')
        h3.cmd(f'iperf3 -c {h7.IP()} -p 5000 -b 10M -P 10 -t 150 -C {cc_scheme}')

    elif option == 'c2c':
        # Part (c) condition 2c: Clients on H1, H3, and H4
        h1.cmd(f'iperf3 -c {h7.IP()} -p 5000 -b 10M -P 10 -t 150 -C {cc_scheme}')
        h3.cmd(f'iperf3 -c {h7.IP()} -p 5000 -b 10M -P 10 -t 150 -C {cc_scheme}')
        h4.cmd(f'iperf3 -c {h7.IP()} -p 5000 -b 10M -P 10 -t 150 -C {cc_scheme}')

    else:
        info('*** Invalid experiment option. Please use one of: a, b, c1, c2a, c2b, or c2c\n')
        net.stop()
        sys.exit(1)

    info('*** Running CLI (use exit to terminate the experiment)...\n')
    CLI(net)
    net.stop()

if __name__ == '__main__':
    # Expect at least 3 arguments: <option> <cc_scheme> [loss]
    if len(sys.argv) < 3:
        print("Usage: sudo python3 script.py <option> <cc_scheme> [loss]")
        print("  <option>: a, b, c1, c2a, c2b, or c2c")
        print("  <cc_scheme>: TCP congestion control scheme (e.g., reno, cubic, bbr)")
        print("  [loss]: Optional. Link loss percentage for link S2-S3 (default 0)")
        sys.exit(1)

    exp_option = sys.argv[1]
    cc_scheme = sys.argv[2]
    # Link loss percentage: if provided, convert to int; else default to 0
    loss = int(sys.argv[3]) if len(sys.argv) >= 4 else 0

    run_experiment(exp_option, cc_scheme, link_loss=loss)
