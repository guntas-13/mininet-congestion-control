#!/usr/bin/python
from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import Controller, OVSKernelSwitch
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel, info
import time

class CustomTopo(Topo):
    def build(self):
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
        
        # Connect switches; note the s3-s4 link is limited to 10Mbps.
        self.addLink(s1, s2)
        self.addLink(s2, s3)
        self.addLink(s3, s4, bw=10)

def runIperf(net):
    h1 = net.get('h1')
    h7 = net.get('h7')
    
    # Start the iperf3 server on h7 in daemon mode.
    info("*** Starting iperf3 server on h7\n")
    h7.cmd('iperf3 -s -p 5000 -D')
    time.sleep(2)  # Allow time for the server to start
    
    # Run the iperf3 client on h1, setting target bandwidth (-b) to 100M and using cubic.
    info("*** Running iperf3 client on h1\n")
    result = h1.cmd('iperf3 -c {} -b 100M -p 5000 -t 20 -i 0.2 -C cubic'.format(h7.IP()))
    info(result)
    
    # Optionally, check TCP socket details to observe congestion window values
    info("*** TCP socket details on h1 (using ss -tin):\n")
    cwnd_info = h1.cmd('ss -tin')
    info(cwnd_info)

def main():
    setLogLevel('info')
    # Use TCLink to enforce link bandwidth limitations.
    net = Mininet(topo=CustomTopo(), controller=Controller,
                  switch=OVSKernelSwitch, link=TCLink)
    net.start()
    
    runIperf(net)
    
    # Drop to CLI for further interactive inspection.
    # CLI(net)
    net.stop()

if __name__ == '__main__':
    main()
