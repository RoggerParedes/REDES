from mininet.topo import Topo
from mininet.link import TCLink

topos = {
    'default_test': (lambda: MyTopo(3, 10)),
    'mytopo': (lambda n_host, loss: MyTopo(n_host, loss))
}


class MyTopo(Topo):
    def __init__(self, n_host, loss):
        Topo.__init__(self)
        server = self.addHost('Server')
        switch = self.addSwitch('s1')
        self.addLink(server, switch, cls=TCLink, loss=loss)
        for i in range(0, n_host):
            generic_node = self.addHost('host_' + (str(i + 1)))
            self.addLink(switch, generic_node, cls=TCLink, loss=loss)