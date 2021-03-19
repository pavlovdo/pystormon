#!/usr/bin/env python3


class NetworkDevice:
    """ base class for network devices """

    def __init__(self, hostname, ip, login=None, password=None):

        self.hostname = hostname
        self.ip = ip
        self.login = login
        self.password = password


class WBEMDevice(NetworkDevice):
    """ class for WBEM devices """

    def Connect(self, namespace='root/ibm', printing=False):

        from pywbem import WBEMConnection

        server_uri = f'https://{self.ip.rstrip()}'

        conn = WBEMConnection(server_uri, (self.login, self.password),
                              namespace, no_verification=True)

        return conn
