#!/usr/bin/python3

"""
Mininet TCP Congestion Control Experiment Script

This script sets up a Mininet topology with 7 hosts (H1–H7) connected via 4 switches (S1–S4)
and runs iperf3-based TCP experiments using different TCP congestion control schemes.

Experiments:
    a. Default topology:
         - Run client on H1 for 150s and server on H7.
         - Measure throughput over time, goodput, packet loss rate, and maximum window size.
    b. Default topology with staggered clients:
         - H1 starts at T=0s (runs for 150s), H3 at T=15s (120s), H4 at T=30s (90s) with server on H7.
    c. Topology changes:
         1. Option c1 (“s2s4”): Activate a direct link between S2 and S4 (bw=100 Mbps) and run the client on H3.
         2. Options c2a, c2b, c2c (“s1s4”): Activate a direct link between S1 and S4 (bw=100 Mbps) while ensuring hosts on S2 and S3 can reach S1.
              - c2a: Clients on H1 and H2.
              - c2b: Clients on H1 and H3.
              - c2c: Clients on H1, H3, and H4.
    d. For any experiment above, an optional loss value (e.g., 1% or 5%) may be specified for the bottleneck link.

Usage:
    sudo python3 script.py <option> <cc_scheme> [loss]

    <option>: a, b, c1, c2a, c2b, or c2c
    <cc_scheme>: TCP congestion control scheme (e.g., reno, cubic, bbr)
    [loss]: Optional. Packet loss percentage for the bottleneck link (default 0)
"""

import sys
import time
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Controller, OVSKernelSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info

class CustomTopo(Topo):
    def build(self, topo_type="default", link_loss=0, bandwidths=None):
        """
        Builds the topology based on the experiment type.
        
        :param topo_type: Type of topology. Options:
                          - "default": Use links S1-S2, S2-S3, and S3-S4.
                          - "s2s4": For experiment c1. Use S1-S2 and a direct S2-S4 link.
                          - "s1s4": For experiment c2. Use S1-S2, S1-S3 and a direct S1-S4 link.
        :param link_loss: Packet loss percentage applied on the bottleneck link.
        :param bandwidths: Dictionary specifying link bandwidths. If None, no bandwidth is set.
        """
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

        # Connect hosts to switches:
        self.addLink(h1, s1)
        self.addLink(h2, s1)
        self.addLink(h3, s2)
        self.addLink(h4, s3)
        self.addLink(h5, s3)
        self.addLink(h6, s4)
        self.addLink(h7, s4)

        if topo_type == "s2s3":
            self.addLink(s1, s2, bw=bandwidths.get('s1-s2', None))
            self.addLink(s2, s3, bw=bandwidths.get('s2-s3', None), loss=link_loss)
            self.addLink(s3, s4, bw=bandwidths.get('s3-s4', None))
        else:
            # Fallback to default topology if topo_type is unrecognized.
            self.addLink(s1, s2)
            self.addLink(s2, s3, loss=link_loss)
            self.addLink(s3, s4)

def run_experiment(option, cc_scheme, link_loss=0):
    """
    Sets up the network, starts the iperf3 server, and runs the appropriate client(s)
    based on the selected experiment option.
    
    :param option: Experiment option (a, b, c1, c2a, c2b, or c2c)
    :param cc_scheme: TCP congestion control scheme (e.g., reno, cubic, bbr)
    :param link_loss: Packet loss percentage for the bottleneck link.
    """
    setLogLevel('info')

    # Determine the topology type and bandwidth configuration (all set to 100 Mbps by default)
    if option in ['c1', 'c2a', 'c2b', 'c2c']:
        topo_type = "s2s3"
        bw = {'s1-s2': 100, 's2-s3': 50, 's3-s4': 100}
    elif option in ['a', 'b']:
        topo_type = "default"
        bw = None
    else:
        info('*** Invalid experiment option. Please use one of: c1, c2a, c2b, or c2c\n')
        sys.exit(1)

    # Create network with custom topology
    net = Mininet(topo=CustomTopo(topo_type=topo_type, link_loss=link_loss, bandwidths=bw),
                  controller=Controller,
                  switch=OVSKernelSwitch,
                  autoSetMacs=True)
    info('*** Starting network\n')
    net.start()
    net.staticArp()
    net.pingAll()

    # Get hosts
    h1, h2, h3, h4, h5, h6, h7 = net.get('h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'h7')

    # Start the iperf3 server on H7 (running in the background)
    info('*** Starting iperf3 server on H7\n')
    h7.cmd('iperf3 -s -p 5000 -D')
    
    input('Press Enter to start the experiment...')

    info('*** Starting iperf3 client(s) with congestion control scheme: %s\n' % cc_scheme)
    if option == 'a':
        # Run client on H1 for 150 seconds.
        h1.cmd(f'iperf3 -c {h7.IP()} -p 5000 -b 10M -P 10 -t 150 -C {cc_scheme} > temp.txt')
    elif option == 'b':
        # Staggered clients: H1 at T=0 (150s), H3 at T=15 (120s), H4 at T=30 (90s).
        h1.cmd(f'iperf3 -c {h7.IP()} -p 5000 -b 10M -P 10 -t 150 -C {cc_scheme} &')
        time.sleep(15)
        h3.cmd(f'iperf3 -c {h7.IP()} -p 5000 -b 10M -P 10 -t 120 -C {cc_scheme} &')
        time.sleep(15)
        h4.cmd(f'iperf3 -c {h7.IP()} -p 5000 -b 10M -P 10 -t 90 -C {cc_scheme} &')
    elif option == 'c1':
        # Direct link (S2–S4): Run client on H3 for 150 seconds.
        h3.cmd(f'iperf3 -c {h7.IP()} -p 5000 -b 10M -P 10 -t 150 -C {cc_scheme}')
    elif option == 'c2a':
        # Direct link (S1–S4): Run clients on H1 and H2 for 150 seconds.
        h1.cmd(f'iperf3 -c {h7.IP()} -p 5000 -b 10M -P 10 -t 150 -C {cc_scheme} &')
        h2.cmd(f'iperf3 -c {h7.IP()} -p 5000 -b 10M -P 10 -t 150 -C {cc_scheme}')
    elif option == 'c2b':
        # Direct link (S1–S4): Run clients on H1 and H3 for 150 seconds.
        h1.cmd(f'iperf3 -c {h7.IP()} -p 5000 -b 10M -P 10 -t 150 -C {cc_scheme} &')
        h3.cmd(f'iperf3 -c {h7.IP()} -p 5000 -b 10M -P 10 -t 150 -C {cc_scheme}')
    elif option == 'c2c':
        # Direct link (S1–S4): Run clients on H1, H3, and H4 for 150 seconds.
        h1.cmd(f'iperf3 -c {h7.IP()} -p 5000 -b 10M -P 10 -t 150 -C {cc_scheme} &')
        h3.cmd(f'iperf3 -c {h7.IP()} -p 5000 -b 10M -P 10 -t 150 -C {cc_scheme} &')
        h4.cmd(f'iperf3 -c {h7.IP()} -p 5000 -b 10M -P 10 -t 150 -C {cc_scheme}')
    else:
        info('*** Invalid experiment option. Please use one of: a, b, c1, c2a, c2b, or c2c\n')
        net.stop()
        sys.exit(1)

    info('*** Running CLI (type "exit" or press <Ctrl-D> to terminate the experiment)...\n')
    CLI(net)
    net.stop()

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: sudo python3 script.py <option> <cc_scheme> [loss]")
        print("  <option>: a, b, c1, c2a, c2b, or c2c [Note: d part can be run using c1, c2a, c2b, or c2c with loss value]")
        print("  <cc_scheme>: TCP congestion control scheme (e.g., reno, cubic, bbr)")
        print("  [loss]: Optional. Packet loss percentage for the bottleneck link (s2-s3) (default 0)")
        sys.exit(1)

    exp_option = sys.argv[1]
    cc_scheme = sys.argv[2]
    loss = int(sys.argv[3]) if len(sys.argv) >= 4 else 0

    run_experiment(exp_option, cc_scheme, link_loss=loss)
