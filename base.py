import sys
import time
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Controller, OVSKernelSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info

class CustomTopo(Topo):
    def build(self):
        """
        Builds the topology.
        :param link_loss: Packet loss percentage for the link between S2 and S3.
        :param bandwidths: Dictionary defining bandwidth for switch links.
                           Expected keys: 's1-s2', 's2-s3', 's3-s4'
        """
        # if bandwidths is None:
        #     # Default bandwidths (in Mbps) as specified in part (c)
        #     bandwidths = {'s1-s2': 100, 's2-s3': 50, 's3-s4': 100}

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
        self.addLink(s1, s2, bw=50)
        self.addLink(s2, s3, bw=50)
        self.addLink(s3, s4, bw=50)


topos = { 'mytopo': ( lambda: CustomTopo() ) }

if __name__ == '__main__':
    # setLogLevel('info') # set Mininet log level: debug, info, warning, error

    net = Mininet(topo=CustomTopo(), controller=Controller, switch=OVSKernelSwitch)
    
    net.start()
    # info('*** Running CLI\n')
    CLI(net)
    net.stop()
