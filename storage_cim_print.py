#!/usr/bin/env python3

#
# IBM Storwize CIM print
#
# 2020 Denis Pavlov
#
# Print names and values of properties of storage CIM classes from monitored_properies.json
#

import os
import sys

from configread import configread
from json import load
from pynetdevices import WBEMDevice
from pywbem import _exceptions


def main():

    # get script name
    software = sys.argv[0]

    # set project name as current directory name
    project = os.path.abspath(__file__).split('/')[-2]

    # get config file name
    conf_file = (
        f'/etc/zabbix/externalscripts/{project}/conf.d/{project}.conf')

    # read network device parameters from config and save it to dict
    nd_parameters = configread(conf_file, 'NetworkDevice', 'device_file',
                               'login', 'password', 'name_space')

    # read storage device parameters from config and save it to another dict
    sd_parameters = configread(conf_file, 'StorageDevice',
                               'monitored_properties_file')

    # form dictionary of matching storage concepts and cim properties
    # more details in https://www.ibm.com/support/knowledgecenter/STHGUJ_8.3.1/com.ibm.storwize.v5000.831.doc/svc_conceptsmaptocimconcepts_3skacv.html
    with open(sd_parameters['monitored_properties_file'], "r") as monitored_properties_file:
        monitored_properties = load(monitored_properties_file)

    # get variables
    login = nd_parameters['login']
    password = nd_parameters['password']

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

            # print all properties for all instances (objects) for cim classes from dict sc_maps
            for storage_concept in monitored_properties:
                storage_cim_class = monitored_properties[storage_concept]['cim_class']

                # try to request storage via WBEM
                try:
                    instances = conn.EnumerateInstances(storage_cim_class,
                                                        namespace=nd_parameters['name_space'])
                except _exceptions.AuthError as error:
                    print((f'{project}_error: exception in {software}: can\'t exec query on {device_name}: {error}. '
                           f'Check your username/password and permissions of user.'),
                          file=sys.stderr)
                    exit(1)
                except _exceptions.ConnectionError as error:
                    print((f'{project}_error: exception in {software}: can\'t exec query on {device_name}: {error}. '
                           f'Check the connection to storage or try later.'),
                          file=sys.stderr)
                    exit(1)
                except:
                    print(f'{project}_error: exception in {software}: {sys.exc_info()}',
                          file=sys.stderr)
                    exit(1)

                for instance in instances:
                    for prop_name, prop_value in instance.items():
                        print(
                            (f'Device: {device_name}, Concept: {storage_concept}, '
                             f'CIM class: {storage_cim_class}\nProperty: {prop_name}, '
                             f'Value: {prop_value}\n'))

    device_list_file.close()


if __name__ == "__main__":
    main()
