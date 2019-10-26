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
conf_file = ('/etc/zabbix/externalscripts/' + os.path.abspath(__file__).split('/')[-2] + '/'
             + os.path.abspath(__file__).split('/')[-2] + '.conf')

nd_parameters = configread(conf_file, 'NetworkDevice', 'device_file', 'login', 'password',
                           'name_space')

# open file with list of monitored storages
device_list_file = open(nd_parameters['device_file'])

# dictionary of matching storwize concepts and cim properties
# https://www.ibm.com/support/knowledgecenter/STHGUJ/com.ibm.storwize.v5000.710.doc/svc_conceptsmaptocimconcepts_3skacv.html
storwize_cim = {'Array': 'IBMTSSVC_Array', 'DiskDrive': 'IBMTSSVC_DiskDrive',
                'mdisk': 'IBMTSSVC_BackendVolume', 'VDisk': 'IBMTSSVC_StorageVolume' }

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

        # print all parameters for all instances (objects) for cim from storwize_cim
        for storwize_concept in storwize_cim:
            cim_name = storwize_cim[storwize_concept]
            instances = conn.EnumerateInstances(cim_name,namespace=nd_parameters['name_space'])
            print (storwize_concept)
            for instance in instances:
                for prop_name, prop_value in instance.items():
                    print('  %s: %r' % (prop_name, prop_value))
