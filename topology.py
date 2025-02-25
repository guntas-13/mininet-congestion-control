#!/usr/bin/python

from mininet.topo import Topo

class CustomTopo(Topo):
    def build(self):
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
        self.addLink(s1, s2)
        self.addLink(s2, s3)
        self.addLink(s3, s4)

topos = { 'mytopo': ( lambda: CustomTopo() ) }

"""
h7 iperf3 -s -D
h1 iperf3 -c 10.0.0.1 -p 5001 -b 10M -P 10 -t 150 -C cubic
h1 iperf3 -c 10.0.0.1 -p 5001 -b 10M -P 10 -t 150 -C scalable
h1 iperf3 -c 10.0.0.1 -p 5001 -b 10M -P 10 -t 150 -C westwood
"""