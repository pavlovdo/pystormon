#!/usr/bin/env python3

import os
import requests
import socket

from configread import configread
from pyzabbix import ZabbixSender
from socket import timeout
from sys import stderr

# set project name as current directory name
project = os.path.abspath(__file__).split('/')[-2]

# get config file name
conf_file = (
    f'/etc/zabbix/externalscripts/{project}/conf.d/{project}.conf')

# read network device parameters from config and save it to dict
nd_parameters = configread(conf_file, 'NetworkDevice',
                           'slack_hook', 'zabbix_server')

# get variables for error notifications
slack_hook = nd_parameters['slack_hook']
zabbix_server = nd_parameters['zabbix_server']

hostname = socket.gethostname()


def slack_post(software, message, icon_emoji=':snake:'):
    """ post alarms to slack channel """

    if slack_hook:
        requests.post(slack_hook, json={'username': hostname,
                                        'icon_emoji': icon_emoji,
                                        'text': f'{project}_error: exception in {software}: {message}'})


def zabbix_send(data, printing, software):
    """ send packet of data to zabbix """

    try:
        zabbix_send_status = ZabbixSender(zabbix_server).send(data)
        if printing:
            print(
                f'Status of sending data to zabbix:\n{zabbix_send_status}')
    except timeout as error:
        print(
            (f'{project}_error: exception in {software}: Zabbix trapper socket timeout on {zabbix_server}: {error}. '
                f'Check health status of zabbix server.'),
            file=stderr)
        slack_post(
            software,
            (f'Zabbix trapper socket timeout on {zabbix_server}: {error}. '
                f'Check health status of zabbix server.'))
        exit(1)
    except ConnectionRefusedError as error:
        print(
            (f'{project}_error: exception in {software}: Zabbix trapper refused connection on {zabbix_server}: {error}. '
                f'Check running of zabbix trappers and firewall trafic permissions.'),
            file=stderr)
        slack_post(
            software,
            (f'Zabbix trapper refused connection on {zabbix_server}: {error}. '
                f'Check running of zabbix trappers and firewall trafic permissions.'))
        exit(1)
    except ConnectionResetError as error:
        print(
            (f'{project}_error: exception in {software}: Zabbix trapper reset connection on {zabbix_server}: {error}. '
                f'Check running of zabbix trappers.'),
            file=stderr)
        slack_post(
            software,
            (f'Zabbix trapper reset connection on {zabbix_server}: {error}. '
                f'Check running of zabbix trappers.'))
        exit(1)
