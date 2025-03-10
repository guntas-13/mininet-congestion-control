"""
Mininet TCP Congestion Control Experiment Script

This script sets up a Mininet topology with 7 hosts (H1-H7) connected via 4 switches (S1-S4)
and runs iperf3-based TCP experiments using different TCP congestion control schemes.

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
from mininet.link import TCLink

class CustomTopo(Topo):
    def build(self, option, link_loss=0):
        # Switches
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        s3 = self.addSwitch('s3')
        s4 = self.addSwitch('s4')

        # Hosts
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        h3 = self.addHost('h3')
        h4 = self.addHost('h4')
        h5 = self.addHost('h5')
        h6 = self.addHost('h6')
        h7 = self.addHost('h7')

        # Links
        self.addLink(h1, s1)
        self.addLink(h2, s1)
        self.addLink(h3, s2)
        self.addLink(h4, s3)
        self.addLink(h5, s3)
        self.addLink(h6, s4)
        self.addLink(h7, s4)

        if option in ['c1', 'c2a', 'c2b', 'c2c']:
            self.addLink(s1, s2, bw=100)
            self.addLink(s2, s3, bw=50, loss=link_loss)
            self.addLink(s3, s4, bw=100)
        else:
            self.addLink(s1, s2)
            self.addLink(s2, s3)
            self.addLink(s3, s4)

def run_experiment(option, cc_scheme, link_loss=0):
    setLogLevel('info')

    VALID_OPTIONS = {'a', 'b', 'c1', 'c2a', 'c2b', 'c2c'}

    prefix = 'd_' if link_loss > 0 else ''
    suffix = f'_{link_loss}' if link_loss > 0 else ''

    if option not in VALID_OPTIONS:
        info('*** Invalid experiment option. Please use one of: a, b, c1, c2a, c2b, or c2c\n')
        net.stop()
        sys.exit(1)

    net = Mininet(topo=CustomTopo(option=option, link_loss=link_loss),
                  controller=Controller,
                  switch=OVSKernelSwitch,
                  link=TCLink)
    info('*** Starting network\n')
    net.start()
    net.staticArp()
    net.pingAll()

    h1, h2, h3, h4, h5, h6, h7 = net.get('h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'h7')
    server_ip = h7.IP()

    info('*** Starting iperf3 server on H7\n')
    def run_server(port):
        h7.cmd(f'iperf3 -s -p {port} -D')
        
    run_server(5000)
    
    input('Press Enter to start the experiment (You may start you wireshark now)...')
    # At this point you can start wireshark and start capturing packets on 's4-eth2' (this will change if you'll change the order in which links are created in the topology) interface which is connected to h7 (the server) to capture the traffic.

    info('*** Starting iperf3 client(s) with congestion control scheme: %s\n' % cc_scheme)

    # Part A
    if option == 'a':
        h1.cmd(f'iperf3 -c {server_ip} -p 5000 -b 10M -P 10 -t 150 -C {cc_scheme} > ./logs/a_h1_{cc_scheme}.txt')

    # Part B
    elif option == 'b':
        run_server(5001)
        run_server(5002)
        h1.cmd(f'iperf3 -c {server_ip} -p 5000 -b 10M -P 10 -t 150 -C {cc_scheme} > ./logs/b_h1_{cc_scheme}.txt &')
        time.sleep(15)
        h3.cmd(f'iperf3 -c {server_ip} -p 5001 -b 10M -P 10 -t 120 -C {cc_scheme} > ./logs/b_h3_{cc_scheme}.txt &')
        time.sleep(15)
        h4.cmd(f'iperf3 -c {server_ip} -p 5002 -b 10M -P 10 -t 90 -C {cc_scheme} > ./logs/b_h4_{cc_scheme}.txt &')

    # Part C/D
    else:  # option is one of: c1, c2a, c2b, c2c
        if option == 'c1':
            h3.cmd(f'iperf3 -c {server_ip} -p 5000 -b 10M -P 10 -t 150 -C {cc_scheme} > ./logs/{prefix}c1_h3_{cc_scheme}{suffix}.txt &')
        
        elif option == 'c2a':
            run_server(5001)
            h1.cmd(f'iperf3 -c {server_ip} -p 5000 -b 10M -P 10 -t 150 -C {cc_scheme} > ./logs/{prefix}c2a_h1_{cc_scheme}{suffix}.txt &')
            h2.cmd(f'iperf3 -c {server_ip} -p 5001 -b 10M -P 10 -t 150 -C {cc_scheme} > ./logs/{prefix}c2a_h2_{cc_scheme}{suffix}.txt &')
        
        elif option == 'c2b':
            run_server(5001)
            h1.cmd(f'iperf3 -c {server_ip} -p 5000 -b 10M -P 10 -t 150 -C {cc_scheme} > ./logs/{prefix}c2b_h1_{cc_scheme}{suffix}.txt &')
            h3.cmd(f'iperf3 -c {server_ip} -p 5001 -b 10M -P 10 -t 150 -C {cc_scheme} > ./logs/{prefix}c2b_h3_{cc_scheme}{suffix}.txt &')
        
        elif option == 'c2c':
            run_server(5001)
            run_server(5002)
            h1.cmd(f'iperf3 -c {server_ip} -p 5000 -b 10M -P 10 -t 150 -C {cc_scheme} > ./logs/{prefix}c2c_h1_{cc_scheme}{suffix}.txt &')
            h3.cmd(f'iperf3 -c {server_ip} -p 5001 -b 10M -P 10 -t 150 -C {cc_scheme} > ./logs/{prefix}c2c_h3_{cc_scheme}{suffix}.txt &')
            h4.cmd(f'iperf3 -c {server_ip} -p 5002 -b 10M -P 10 -t 150 -C {cc_scheme} > ./logs/{prefix}c2c_h4_{cc_scheme}{suffix}.txt &')

    info('*** Running CLI (type "exit" or press <Ctrl-D> to terminate the experiment)...\n')
    CLI(net)
    net.stop()

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: sudo python3 script.py <option> <cc_scheme> [loss]")
        print("  <option>: a, b, c1, c2a, c2b, or c2c. d can be run by passing loss with c1, c2a, c2b, or c2c")
        print("  <cc_scheme>: TCP congestion control scheme (e.g., reno, cubic, bbr)")
        print("  [loss]: Optional. Packet loss percentage for the bottleneck link (default 0)")
        sys.exit(1)

    exp_option = sys.argv[1]
    cc_scheme = sys.argv[2]
    loss = int(sys.argv[3]) if len(sys.argv) >= 4 else 0

    run_experiment(exp_option, cc_scheme, link_loss=loss)