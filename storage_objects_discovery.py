#!/usr/bin/env python3

#
# IBM Storwize objects discovery for Zabbix
#
# 2016-2020 Denis Pavlov
#
# Discover storage objects from Storwize including physical and logical disks, via CIM/WBEM and sends it to Zabbix Server via Zabbix Sender API
#
# Use with template Template Storage Pystormon
#

import os
import sys

from configread import configread
from functions import slack_post, zabbix_send
from json import load
from pynetdevices import WBEMDevice
from pywbem import _exceptions
from pyzabbix import ZabbixMetric


# set project as current directory name, software as name of current script
project = os.path.abspath(__file__).split('/')[-2]
software = sys.argv[0]


def storage_objects_discovery(wbem_connection, storage_name, cim_class, cim_property_name):
    """ get list of storage objects """

    # create empty list for storage object names
    result = []

    # form "SELECT" request string
    request = f'SELECT {cim_property_name} FROM {cim_class}'

    # try to request storage via WBEM
    try:
        storage_response = wbem_connection.ExecQuery('DMTF:CQL', request)
    except _exceptions.ConnectionError as error:
        print(f'{project}_error: exception in {software}: can\'t exec query on {storage_name}: {error}',
              file=sys.stderr)
        slack_post(software, f'can\'t exec query on {storage_name}: {error}')
        exit(1)
    except:
        print(f'{project}_error: exception in {software}: {sys.exc_info()}',
              file=sys.stderr)
        slack_post(software, sys.exc_info())
        exit(1)

    # parse reply and form a list of storage objects
    for cim_object in storage_response:
        object_name = cim_object.properties[cim_property_name].value
        result.append(object_name)

    return result


def main():

    # get config file name
    conf_file = (
        f'/etc/zabbix/externalscripts/{project}/conf.d/{project}.conf')

    # read network device parameters from config and save it to dict
    nd_parameters = configread(conf_file, 'NetworkDevice', 'device_file',
                               'login', 'password', 'name_space', 'printing')

    # read storage device parameters from config and save it to another dict
    sd_parameters = configread(conf_file, 'StorageDevice',
                               'storage_cim_map_file')

    # get printing boolean variable from config for debugging enable/disable
    printing = eval(nd_parameters['printing'])

    # get variables
    login = nd_parameters['login']
    password = nd_parameters['password']

    # form dictionary of matching storage concepts and cim properties
    # more details in https://www.ibm.com/support/knowledgecenter/STHGUJ_8.3.1/com.ibm.storwize.v5000.831.doc/svc_conceptsmaptocimconcepts_3skacv.html
    with open(sd_parameters['storage_cim_map_file'], "r") as storage_cim_map_file:
        sc_maps = load(storage_cim_map_file)

    # open config file with list of monitored storages
    device_list_file = open(nd_parameters['device_file'])

    # unpack storage list to variables
    for device_line in device_list_file:
        device_type, device_name, device_ip = device_line.split(':')
        device_ip = device_ip.rstrip('\n')

        # connect to each storage via WBEM, get conn object
        if device_type == 'storwize':
            device = WBEMDevice(device_name, device_ip, login, password)
            # get namespace from config, root/ibm by default
            namespace = nd_parameters.get('name_space', 'root/ibm')
            conn = device.Connect(namespace)

            # initialize packet for sending to zabbix
            packet = []

            # iterate through dictionary of monitored storage concepts
            for storage_concept in sc_maps:
                # get list of storage objects
                so_names = storage_objects_discovery(conn, device_name,
                                                     sc_maps[storage_concept]['cim_class'],
                                                     sc_maps[storage_concept]['cim_property_name'])

                so_names_dict = {}
                so_names_list = []

                # create list of disk types and names in JSON
                for so_name in so_names:
                    so_name_json = {"{#SO_TYPE}": storage_concept,
                                    "{#SO_NAME}": so_name}
                    so_names_list.append(so_name_json)

                # form data for send to zabbix
                so_names_dict['data'] = so_names_list

                trapper_key = sc_maps[storage_concept]['zabbix_discovery_key']
                trapper_value = str(so_names_dict).replace("\'", "\"")

                # form packet for sending to zabbix
                packet.append(ZabbixMetric(device_name, trapper_key,
                                           trapper_value))

                # print data for visual check
                if printing:
                    print(device_name)
                    print(trapper_key)
                    print(trapper_value)

            # trying send data to zabbix
            zabbix_send(packet, printing, software)

    device_list_file.close()


if __name__ == "__main__":
    main()
else:
    print("Please execute this program as main\n")
