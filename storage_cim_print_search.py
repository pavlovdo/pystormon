#!/usr/bin/env python3

#
# IBM Storwize CIM print
#
# 2020 - 2021 Denis Pavlov
#
# Print CIM properties of Storwize classes with names set by search string to stdout and detected_properties_file
#

import os
import sys

from configread import configread
from json import load
from pynetdevices import WBEMDevice
from pywbem import _exceptions


def main():

    # set project name as current directory name
    project = os.path.abspath(__file__).split('/')[-2]

    software = sys.argv[0]

    if len(sys.argv) == 1:
        print((f'Please add argument(s) to call of program for search Storage CIM classes: \n'
               f'Example of syntax: {software} Array Volume'))
        exit(1)

    search_strings = sys.argv[1:]

    # get config file name
    conf_file = (
        f'/etc/zabbix/externalscripts/{project}/conf.d/{project}.conf')

    # read network device parameters from config and save it to dict
    nd_parameters = configread(conf_file, 'NetworkDevice', 'device_file',
                               'login', 'name_space', 'password')

    sd_parameters = configread(
        conf_file, 'StorageDevice', 'detected_properties_file')

    # get variables
    login = nd_parameters['login']
    password = nd_parameters['password']

    # open config file with list of monitored storages
    device_list_file = open(nd_parameters['device_file'])

    # open properties file for writing
    detected_properties_file = open(
        sd_parameters['detected_properties_file'], 'w')

    # unpack storage list to variables
    for device_line in device_list_file:
        device_type, device_name, device_ip = device_line.split(':')
        device_ip = device_ip.rstrip('\n')

        # connect to each storage via WBEM, get conn object
        if device_type == 'storwize':
            device = WBEMDevice(device_name, device_ip, login, password)
            # get namespace from config, root/ibm by default
            namespace = nd_parameters.get('name_space', 'root/ibm')

            print(f'Connecting to {device_name} ...')
            conn = device.Connect(namespace)

            # try to get all cim classes from storage via WBEM
            try:
                sc_cim_classes = conn.EnumerateClassNames(
                    namespace=nd_parameters['name_space'], DeepInheritance=True)
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

            # try to get all instances for each cim class from storage via WBEM
            for sc_cim_class in sc_cim_classes:
                for search_string in search_strings:
                    if sc_cim_class.find(search_string) > 0:
                        try:
                            instances = conn.EnumerateInstances(sc_cim_class,
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
                                output_string = (f'Device: {device_name}, CIM class: {sc_cim_class}\n'
                                                 f'Property: {prop_name}, Value: {prop_value}\n')
                                print(output_string)
                                detected_properties_file.write(
                                    f'{output_string} \n')

    device_list_file.close()
    detected_properties_file.close()


if __name__ == "__main__":
    main()
