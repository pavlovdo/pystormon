#!/usr/bin/env python3

#
# IBM Storwize performance monitoring script for Zabbix
#
# 2018 Denis Pavlov 
#
# Get perfomance statistic from Storwize via CIM/WBEM and sends it to Zabbix via Zabbix Sender API
#
# Use with template Template Storage Pystormon
#

import os

from configread import configread
from pynetdevices import WBEMDevice
from pyzabbix import ZabbixMetric, ZabbixSender


def disks_perf(wbem_connection, disk_table, disk_name_column, perf_table, perf_counters_names):
    """ get performance statistics for disks """

    disks_names_list = []
    disks_perfs_list = []
    disks_perfs_dict = {}

    # form "SELECT" request strings
    disks_request = 'SELECT ' + disk_name_column + ' FROM ' + disk_table
    perf_request = 'SELECT ' + ','.join(perf_counters_names) + ' FROM ' + perf_table
   
    # request storage via WBEM
    disks_names_cim = wbem_connection.ExecQuery('DMTF:CQL', disks_request)
    disks_perfs_cim = wbem_connection.ExecQuery('DMTF:CQL', perf_request)

    # form list of storage disks
    for disk_name_cim in disks_names_cim:
        disks_names_list.append(disk_name_cim.properties[disk_name_column].value)

    # form list of lists of disks perf counters
    for disk_perf_cim in disks_perfs_cim:
        disk_perf_list = []
        for perf_counter_name in perf_counters_names:
            disk_perf_list.append(int(disk_perf_cim.properties[perf_counter_name].value))
        disks_perfs_list.append(disk_perf_list)

    # form dict of disks perf counters
    for disk_name, disk_perf in zip(disks_names_list, disks_perfs_list):
        disks_perfs_dict[disk_name] = disk_perf

    return disks_perfs_dict 


# read parameters from config file
conf_file = ('/etc/zabbix/externalscripts/' + os.path.abspath(__file__).split('/')[-2] + '/'
             + os.path.abspath(__file__).split('/')[-2] + '.conf')

# read parameters and save it to dict for connecting to storage and sending data to zabbix
nd_parameters = configread(conf_file, 'NetworkDevice', 'device_file', 'login', 'password',
                           'name_space', 'zabbix_server')

# open file with list of monitored storages
device_list_file = open(nd_parameters['device_file'])

# create list of perfomance counters names
perf_counters_names = ['ReadIOs', 'WriteIOs', 'TotalIOs', 'KBytesRead', 'KBytesWritten', 'KBytesTransferred',
                       'ReadHitIOs', 'WriteHitIOs']

# create dictionary of monitored entities with it WBEMs parameters
disk_types = {'Volume': ['IBMTSSVC_StorageVolume', 'VolumeName', 'IBMTSSVC_StorageVolumeStatistics']}

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

        # get statistic for storage disk types
        for disk_type in disk_types:
            disk_type_perf = disks_perf(conn, disk_types[disk_type][0], disk_types[disk_type][1],
                                        disk_types[disk_type][2], perf_counters_names)

            # get statistic for each storage disk, form data for sending to zabbix
            for disk_name in disk_type_perf:
                for perf_counter_name, perf_counter_value in zip(perf_counters_names, disk_type_perf[disk_name]):
                    trapper_key = perf_counter_name + '[' + disk_type + '.' + disk_name + ']'
                    trapper_value = perf_counter_value

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
