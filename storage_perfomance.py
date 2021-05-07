#!/usr/bin/env python3

#
# IBM Storwize performance monitoring script for Zabbix
#
# 2020 Denis Pavlov
#
# Get perfomance statistic from Storwize via CIM/WBEM and sends it to Zabbix via Zabbix Sender API
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


def storage_objects_get_perf(wbem_connection, storage_name, cim_class, cim_property_name, cim_perf_class, cim_perf_properties):
    """ get performance statistics for storage objects """

    objects_names_list = []
    objects_perfs_list = []
    objects_perfs_dict = {}

    # form "SELECT" request strings
    objects_request = f'SELECT {cim_property_name} FROM {cim_class}'
    str_cim_perf_properties = ','.join(cim_perf_properties)
    perf_request = f'SELECT {str_cim_perf_properties} FROM {cim_perf_class}'

    # try to request storage via WBEM
    try:
        objects_names_cim = wbem_connection.ExecQuery(
            'DMTF:CQL', objects_request)
    except _exceptions.AuthError as error:
        print((f'{project}_error: exception in {software}: can\'t exec query on {storage_name}: {error} '
               f'Check your username/password and permissions of user.'),
              file=sys.stderr)
        slack_post(software, (f'can\'t exec query on {storage_name}: {error} .'
                              f'Check your username/password and permissions of user.'))
        exit(1)
    except _exceptions.ConnectionError as error:
        print((f'{project}_error: exception in {software}: can\'t exec query on {storage_name}: {error}. '
               f'Check the connection to storage or try later.'),
              file=sys.stderr)
        slack_post(software, (f'can\'t exec query on {storage_name}: {error}. '
                              f'Check the connection to storage or try later.'))
        exit(1)
    except _exceptions.HTTPError as error:
        print((f'{project}_error: exception in {software}: WBEM server return code 400 (Bad Request) on {storage_name}: {error}. '
               f'Check the your request.'),
              file=sys.stderr)
        slack_post(software, (f'WBEM server return code 400 (Bad Request) on {storage_name}: {error}. '
                              f'Check the your request {objects_request}.'))
        exit(1)
    except:
        print(f'{project}_error: exception in {software}: {sys.exc_info()}',
              file=sys.stderr)
        slack_post(software, sys.exc_info())
        exit(1)

    try:
        objects_perfs_cim = wbem_connection.ExecQuery('DMTF:CQL', perf_request)
    except _exceptions.AuthError as error:
        print((f'{project}_error: exception in {software}: can\'t exec query on {storage_name}: {error} '
               f'Check your username/password and permissions of user.'),
              file=sys.stderr)
        slack_post(software, (f'can\'t exec query on {storage_name}: {error} .'
                              f'Check your username/password and permissions of user.'))
        exit(1)
    except _exceptions.ConnectionError as error:
        print((f'{project}_error: exception in {software}: can\'t exec query on {storage_name}: {error}. '
               f'Check the connection to storage or try later.'),
              file=sys.stderr)
        slack_post(software, (f'can\'t exec query on {storage_name}: {error}. '
                              f'Check the connection to storage or try later.'))
        exit(1)
    except _exceptions.HTTPError as error:
        print((f'{project}_error: exception in {software}: WBEM server return code 400 (Bad Request) on {storage_name}: {error}. '
               f'Check the your request.'),
              file=sys.stderr)
        slack_post(software, (f'WBEM server return code 400 (Bad Request) on {storage_name}: {error}. '
                              f'Check the your request {perf_request}.'))
        exit(1)
    except:
        print(f'{project}_error: exception in {software}: {sys.exc_info()}',
              file=sys.stderr)
        slack_post(software, sys.exc_info())
        exit(1)

    # form list of storage objects
    for object_name_cim in objects_names_cim:
        objects_names_list.append(
            object_name_cim.properties[cim_property_name].value)

    # form list of lists of objects perf counters
    for object_perf_cim in objects_perfs_cim:
        object_perf_list = []
        for cim_perf_property in cim_perf_properties:
            object_perf_list.append(
                int(object_perf_cim.properties[cim_perf_property].value))
        objects_perfs_list.append(object_perf_list)

    # form dict of objects perf counters
    for object_name, object_perf in zip(objects_names_list, objects_perfs_list):
        objects_perfs_dict[object_name] = object_perf

    return objects_perfs_dict


def main():

    # get config file name
    conf_file = (
        f'/etc/zabbix/externalscripts/{project}/conf.d/{project}.conf')

    # read network device parameters from config and save it to dict
    nd_parameters = configread(conf_file, 'NetworkDevice', 'device_file',
                               'login', 'password', 'name_space', 'printing')

    # read storage device parameters from config and save it to another dict
    sd_parameters = configread(conf_file, 'StorageDevice',
                               'monitored_properties_file')

    # get printing boolean variable from config for debugging enable/disable
    printing = eval(nd_parameters['printing'])

    # get variables
    login = nd_parameters['login']
    password = nd_parameters['password']

    # form dictionary of matching storage concepts and cim properties
    # more details in https://www.ibm.com/support/knowledgecenter/STHGUJ_8.3.1/com.ibm.storwize.v5000.831.doc/svc_conceptsmaptocimconcepts_3skacv.html
    with open(sd_parameters['monitored_properties_file'], "r") as monitored_properties_file:
        monitored_properties = load(monitored_properties_file)

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
            for storage_concept in monitored_properties:
                # get values of object perfomance statistic for all object of each type where perfomance class is given
                if 'cim_perfomance_class' in monitored_properties[storage_concept]:
                    storage_objects_perf = storage_objects_get_perf(conn, device_name,
                                                                    monitored_properties[storage_concept]['cim_class'],
                                                                    monitored_properties[storage_concept]['cim_property_name'],
                                                                    monitored_properties[storage_concept]['cim_perfomance_class'],
                                                                    monitored_properties[storage_concept]['cim_properties_perfomance'])

                    # get statistic for each storage object, form data for sending to zabbix
                    for so_name in storage_objects_perf:
                        for perf_counter_name, perf_counter_value in zip(monitored_properties[storage_concept]['cim_properties_perfomance'],
                                                                         storage_objects_perf[so_name]):
                            trapper_key = f'{perf_counter_name}[{storage_concept}.{so_name}]'
                            trapper_value = perf_counter_value

                            # form list of data for sending to zabbix
                            packet.append(ZabbixMetric(
                                device_name, trapper_key, trapper_value))

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
