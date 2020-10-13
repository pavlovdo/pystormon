#!/usr/bin/env python3


class NetworkDevice:
    """ base class for network devices """

    def __init__(self, hostname, ip, login=None, password=None, enablepw=None,
                 slack_hook=None):

        self.hostname = hostname
        self.ip = ip
        self.login = login
        self.password = password
        self.enablepw = enablepw
        self.slack_hook = slack_hook


class WBEMDevice(NetworkDevice):
    """ class for WBEM devices """

    def Connect(self, namespace='root/ibm', printing=False):

        from pyslack import slack_post
        from pywbem import WBEMConnection
        from sys import exc_info

        server_uri = 'https://' + self.ip.rstrip()
        conn = 0

        try:
            conn = WBEMConnection(server_uri,
                                  (self.login, self.password),
                                  namespace, no_verification=True)
        except:
            if self.slack_hook:
                slack_post(self.slack_hook, 'Unexpected exception in ' +
                           str(self.__class__) + '.' + str(exc_info()),
                           self.hostname, self.ip)

        return conn
