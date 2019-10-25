#!/usr/bin/env python3

#
# IBM Storwize CIM print
#
# 2019 Denis Pavlov 
#
# Print CIM properties of Storwize
#

import os

from configread import configread
from pynetdevices import WBEMDevice

# read parameters from config file
conf_file = ('/etc/orbit/' + os.path.abspath(__file__).split('/')[-2] + '/'
             + os.path.abspath(__file__).split('/')[-2] + '.conf')

# read parameters and save it to dict for connecting to storage and sending data to zabbix
nd_parameters = configread(conf_file, 'NetworkDevice', 'device_file', 'login', 'password',
                           'name_space')

# open file with list of monitored storages
device_list_file = open(nd_parameters['device_file'])

table = 'IBMTSSVC_StorageVolume'

# parse the storage list
for device_line in device_list_file:
    device_params = device_line.split(':')
    device_type = device_params[0]
    device_name = device_params[1]
    device_ip = device_params[2]

    # connect to each storage via WBEM, get conn object
    if device_type == 'storwize':
        device = WBEMDevice(device_name, device_ip, nd_parameters['login'],
                            nd_parameters['password'])
        namespace = nd_parameters.get('name_space', 'root/ibm')
        conn = device.Connect(namespace)

        instances = conn.EnumerateInstances('IBMTSSVC_StorageVolume',namespace=nd_parameters['name_space'])
        for instance in instances:
            for prop_name, prop_value in instance.items():
                print('  %s: %r' % (prop_name, prop_value))
