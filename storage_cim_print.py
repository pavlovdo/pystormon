#!/usr/bin/env python3

#
# IBM Storwize CIM print
#
# 2020 Denis Pavlov
#
# Print CIM properties of Storwize
#

import os

from configread import configread
from json import load
from pynetdevices import WBEMDevice


def main():

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
                               'storage_cim_map_file')

    # form dictionary of matching storage concepts and cim properties
    # more details in https://www.ibm.com/support/knowledgecenter/STHGUJ_8.3.1/com.ibm.storwize.v5000.831.doc/svc_conceptsmaptocimconcepts_3skacv.html
    with open(sd_parameters['storage_cim_map_file'], "r") as storage_cim_map_file:
        sc_maps = load(storage_cim_map_file)

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
            for storage_concept in sc_maps:
                sc_cim_class = sc_maps[storage_concept]['cim_class']
                instances = conn.EnumerateInstances(sc_cim_class,
                                                    namespace=nd_parameters['name_space'])
                print(storage_concept, sc_cim_class)
                for instance in instances:
                    for prop_name, prop_value in instance.items():
                        print('  %s: %r' % (prop_name, prop_value))

    device_list_file.close()


if __name__ == "__main__":
    main()
else:
    print("Please execute this program as main\n")
