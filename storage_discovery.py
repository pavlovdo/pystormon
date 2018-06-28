#!/usr/bin/env python3

#
# IBM Storwize disks discovery for Zabbix
#
# 2018 Denis Pavlov 
#
# Discover physical and logical disks from Storwize via CIM/WBEM and sends it to Zabbix Server via Zabbix Sender API
#
# Use with template Template Storage Pystormon
#

import os

from configread import configread
from pynetdevices import WBEMDevice
from pyzabbix import ZabbixMetric, ZabbixSender


def disks_discovery(wbem_connection, table, name):
    """ get list of storage disks """

    # create empty list for save disk names to it
    result = []

    # form "SELECT" request string
    request = 'SELECT ' + name + ' FROM ' + table

    # request storage via WBEM
    disks_cim = wbem_connection.ExecQuery('DMTF:CQL', request)

    # parse reply and form a list of storage disks
    for disk_cim in disks_cim:
        disk_name = disk_cim.properties[name].value
        result.append(disk_name)

    return result


# read parameters from config file
conf_file = ('/etc/zabbix/externalscripts/' + os.path.abspath(__file__).split('/')[-2] + '/'
             + os.path.abspath(__file__).split('/')[-2] + '.conf')

# read parameters and save it to dict for connecting to storage and sending data to zabbix
nd_parameters = configread(conf_file, 'NetworkDevice', 'device_file', 'login', 'password',
                           'name_space', 'zabbix_server', 'slack_hook')

# open file with list of monitored storages
device_list_file = open(nd_parameters['device_file'])

# form dictionary with disk types, table and column (physical drive, mdisk, volumes etc) for request to storage
disk_types = {'Array': ['IBMTSSVC_Array', 'Name'], 'DiskDrive': ['IBMTSSVC_DiskDrive', 'Name'], 
              'Mdisk': ['IBMTSSVC_BackendVolume', 'Caption'], 'Volume': ['IBMTSSVC_StorageVolume', 'VolumeName']}

# parse the storage list
for device_line in device_list_file:
    device_params = device_line.split(':')
    device_type = device_params[0]
    device_name = device_params[1]
    device_ip = device_params[2]

    # connect to each storage via WBEM, get conn object
    if device_type == 'storwize':
        device = WBEMDevice(device_name, device_ip, nd_parameters['slack_hook'],
                            nd_parameters['login'],
                            nd_parameters['password'])
        namespace = nd_parameters.get('name_space', 'root/ibm')
        conn = device.Connect(namespace)

        packet = []

        for disk_type in disk_types:
            # get list of storage disks
            disks_names = disks_discovery(conn, disk_types[disk_type][0], disk_types[disk_type][1])

            disks_names_dict = {}
            disks_names_list = []

            # create list of disk types and names in JSON
            for disk_name in disks_names:
                disk_name_json = {"{#DISK_TYPE}": disk_type,
                                  "{#DISK_NAME}": disk_name}
                disks_names_list.append(disk_name_json)

            # form data for send to zabbix
            disks_names_dict['data'] = disks_names_list

            if disk_type == 'Volume':
                trapper_key = 'volumes.discovery'
            elif disk_type == 'DiskDrive':
                trapper_key = 'physical.disks.discovery'
            elif disk_type == 'Array':
                trapper_key = 'arrays.discovery'
            elif disk_type == 'Mdisk':
                trapper_key = 'mdisks.discovery'

            trapper_value = str(disks_names_dict).replace("\'", "\"")

            # form list of data for sending to zabbix
            packet.append(ZabbixMetric(device_name, trapper_key, trapper_value))

            # print data for visual check
            print (device_name)
            print (trapper_key)
            print (trapper_value)

        # trying send data to zabbix
        try:
            result = ZabbixSender(nd_parameters['zabbix_server']).send(packet)
        except ConnectionRefusedError as error:
            print ('Unexpected exception in \"ZabbixSender(' + nd_parameters['zabbix_server'] + ').send(packet)\": '
                   + str(error))
            exit(1)
