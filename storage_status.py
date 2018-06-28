#!/usr/bin/env python3

#
# IBM Storwize disk status monitoring script for Zabbix
#
# 2018 Denis Pavlov 
#
# Get status of disk parameters from Storwize via CIM/WBEM and sends it to Zabbix via Zabbix Sender API
#
# Use with template Template Storage Pystormon
#

import os

from configread import configread
from pynetdevices import WBEMDevice
from pyzabbix import ZabbixMetric, ZabbixSender


def disks_get_params(wbem_connection, disk_table, disk_name_column, params_names):
    """ get status of disk parameters """

    # create empty dictionary for save parameters values to it
    disks_params_dict = {}

    # form "SELECT" request string
    disk_drive_select = 'SELECT ' + ','.join(params_names) + ' FROM ' + disk_table

    # request storage via WBEM
    disks_drive_cim = wbem_connection.ExecQuery('DMTF:CQL', disk_drive_select)

    # form dictionary of dictionaries of disk parameters
    for disk_drive_cim in disks_drive_cim:
        disk_params_dict = {} 
        disk_name = disk_drive_cim.properties[disk_name_column].value
        for disk_drive_property in disk_drive_cim.properties:
            if disk_drive_cim.properties[disk_drive_property].value:
                disk_params_dict[disk_drive_property] = disk_drive_cim.properties[disk_drive_property].value
        disks_params_dict[disk_name] = disk_params_dict

    return disks_params_dict 


# read parameters from config file
conf_file = ('/etc/zabbix/externalscripts/' + os.path.abspath(__file__).split('/')[-2] + '/'
             + os.path.abspath(__file__).split('/')[-2] + '.conf')

# read parameters and save it to dict for connecting to storage and sending data to zabbix
nd_parameters = configread(conf_file, 'NetworkDevice', 'device_file', 'login', 'password',
                           'name_space', 'zabbix_server')

# open file with list of monitored storages
device_list_file = open(nd_parameters['device_file'])

# create list of disk drives parameters
disk_params_names = ['DeviceID', 'Name', 'OperationalStatus', 'EnabledState', 'TechType', 'Use', 'ErrorSequenceNumber',
                     'UID', 'Capacity', 'BlockSize', 'MdiskID', 'MdiskName', 'MemberID', 'EnclosureID',
                     'SlotID', 'VendorID', 'ProductID', 'FRUPartNum', 'FRUIdentity', 'RPM', 'FirmwareLevel']

# create dictionary of monitored entities with it WBEMs parameters
disk_types = {'DiskDrive': ['IBMTSSVC_DiskDrive', 'Name', disk_params_names]}

# parse the storage list
for device_line in device_list_file:
    device_params = device_line.split(':')
    device_type = device_params[0]
    device_name = device_params[1]
    device_ip = device_params[2]

    # connect to storage via WBEM, get conn object
    if device_type == 'storwize':
        device = WBEMDevice(device_name, device_ip, nd_parameters['login'],
                            nd_parameters['password'])
        namespace = nd_parameters.get('name_space', 'root/ibm')
        conn = device.Connect(namespace)

        packet = []

        # get values of disk parameters for all disks of each type
        for disk_type in disk_types:
            disk_params = disks_get_params(conn, disk_types[disk_type][0], disk_types[disk_type][1],
                                           disk_types[disk_type][2])

            # get status for each parameter for each storage disk
            for disk_name in disk_params:
                for param_name in disk_params[disk_name]:
                    trapper_key = param_name + '[' + disk_type + '.' + disk_name + ']'
                    trapper_value = disk_params[disk_name][param_name]

                    # form list of data for sending to zabbix
                    packet.append(ZabbixMetric(device_name, trapper_key, trapper_value))

                    # print data for visual check
                    print (device_name)
                    print (trapper_key)
                    print (trapper_value)

        # trying send statistic to zabbix
        try:
            result = ZabbixSender(nd_parameters['zabbix_server']).send(packet)
        except ConnectionRefusedError as error:
            print ('Unexpected exception in \"ZabbixSender(' + nd_parameters['zabbix_server'] + ').send(packet)\": '
                   + str(error))
            exit(1)
