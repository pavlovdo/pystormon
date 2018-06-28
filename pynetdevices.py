#!/usr/bin/env python3


class NetworkDevice:
    """ base class for network devices """
    def __init__(self, hostname, ip, login=None, password=None,
                 enablepw=None):

        self.hostname = hostname
        self.ip = ip
        self.login = login
        self.password = password
        self.enablepw = enablepw


class WBEMDevice(NetworkDevice):
    """ class for WBEM devices """
    def Connect(self, namespace='root/ibm', printing=False):

        import pywbem

        server_uri = 'https://' + self.ip.rstrip()

        try:
            conn = pywbem.WBEMConnection(server_uri, (self.login, self.password),
                                         namespace, no_verification=True)
        except:
            print ('Unexpected exception in \"ZabbixSender(' + nd_parameters['zabbix_server'] +
               ').send(packet)\": '+ str(sys.exc_info()))

        return conn
