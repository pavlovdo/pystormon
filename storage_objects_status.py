#!/usr/bin/env python3

#
# IBM Storwize storage objects status monitoring for Zabbix
#
# 2020 Denis Pavlov
#
# Get status of storage objects parameters from Storwize including physical and logical disks, via CIM/WBEM and sends it to Zabbix via Zabbix Sender API
#
# Use with template Template Storage Pystormon
#

from configread import configread
from json import load
from pynetdevices import WBEMDevice
from pyslack import slack_post
from pyzabbix import ZabbixMetric, ZabbixSender


def storage_objects_get_params(wbem_connection, cim_class, cim_property_name, cim_properties_mon):
    """ get status of disk parameters """

    # create empty dictionary for save storage objects parameters values
    storage_objects = {}

    # form "SELECT" request string
    str_cim_properties_mon = ','.join(cim_properties_mon)
    request = f'SELECT {str_cim_properties_mon} FROM {cim_class}'

    # request storage via WBEM
    storage_response = wbem_connection.ExecQuery('DMTF:CQL', request)

    # form dictionary of dictionaries of disk parameters
    for cim_object in storage_response:
        storage_object = {}
        so_name = cim_object.properties[cim_property_name].value
        for so_property in cim_object.properties:
            if cim_object.properties[so_property].value:
                if type(cim_object.properties[so_property].value) == list:
                    for value in cim_object.properties[so_property].value:
                        index = cim_object.properties[so_property].value.index(
                            value)
                        storage_object[so_property + '.' + str(index)] = value
                else:
                    storage_object[so_property] = cim_object.properties[so_property].value
        storage_objects[so_name] = storage_object

    return storage_objects


def main():

    # set config file name
    conf_file = '/etc/zabbix/externalscripts/pystormon/conf.d/pystormon.conf'

    # read network device parameters from config and save it to dict
    nd_parameters = configread(conf_file, 'NetworkDevice', 'device_file',
                               'login', 'password', 'name_space',
                               'zabbix_server', 'slack_hook')

    # read storage device parameters from config and save it to another dict
    sd_parameters = configread(conf_file, 'StorageDevice',
                               'storage_cim_map_file', 'printing')

    # get printing boolean variable from config for debugging enable/disable
    printing = eval(sd_parameters['printing'])

    # form dictionary of matching storage concepts and cim properties
    # more details in https://www.ibm.com/support/knowledgecenter/STHGUJ_8.3.1/com.ibm.storwize.v5000.831.doc/svc_conceptsmaptocimconcepts_3skacv.html
    with open(sd_parameters['storage_cim_map_file'], "r") as storage_cim_map_file:
        sc_maps = load(storage_cim_map_file)

    # open config file with list of monitored storages
    device_list_file = open(nd_parameters['device_file'])
    device_list_lines = device_list_file.readlines()

    # unpack storage list to variables
    for device_line in device_list_lines:
        device_type, device_name, device_ip = device_line.split(':')

        # connect to storage via WBEM, get conn object
        if device_type == 'storwize':
            device = WBEMDevice(device_name, device_ip,
                                nd_parameters['login'],
                                nd_parameters['password'],
                                nd_parameters['slack_hook'])
            # get namespace from config, root/ibm by default
            namespace = nd_parameters.get('name_space', 'root/ibm')
            conn = device.Connect(namespace)

            # initialize packet for sending to zabbix
            packet = []

            # iterate through dictionary of monitored storage concepts
            for storage_concept in sc_maps:
                # get values of object parameters for all object of each type
                storage_objects = storage_objects_get_params(conn,
                                                             sc_maps[storage_concept]['cim_class'],
                                                             sc_maps[storage_concept]['cim_property_name'],
                                                             sc_maps[storage_concept]['cim_properties_mon'])

                # get status for each parameter for each storage object
                for storage_object in storage_objects:
                    for so_parameter in storage_objects[storage_object]:
                        trapper_key = (so_parameter + '[' + storage_concept
                                       + '.' + storage_object + ']')
                        trapper_value = storage_objects[storage_object][so_parameter]

                        # form list of data for sending to zabbix
                        packet.append(ZabbixMetric(
                            device_name,
                            trapper_key,
                            trapper_value))

                        # print data for visual check
                        if printing:
                            print(device_name)
                            print(trapper_key)
                            print(trapper_value)

            # trying send data to zabbix
            try:
                zabbix_send_status = ZabbixSender(
                    nd_parameters['zabbix_server']).send(packet)
                if printing:
                    print('Status of sending data to zabbix:\n',
                          zabbix_send_status)
            except ConnectionRefusedError as error:
                if nd_parameters['slack_hook']:
                    slack_post(nd_parameters['slack_hook'],
                               'Unexpected exception in \"ZabbixSender()' +
                               '.send(packet)\": ' + str(error),
                               nd_parameters['zabbix_server'])
                exit(1)

    device_list_file.close()


if __name__ == "__main__":
    main()
else:
    print("Please execute this program as main\n")
