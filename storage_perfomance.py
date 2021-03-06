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

from configread import configread
from json import load
from pynetdevices import WBEMDevice
from pyslack import slack_post
from pyzabbix import ZabbixMetric, ZabbixSender


def storage_objects_get_perf(wbem_connection, cim_class, cim_property_name, cim_perf_class, cim_perf_properties):
    """ get performance statistics for storage objects """

    objects_names_list = []
    objects_perfs_list = []
    objects_perfs_dict = {}

    # form "SELECT" request strings
    objects_request = f'SELECT {cim_property_name} FROM {cim_class}'
    str_cim_perf_properties = ','.join(cim_perf_properties)
    perf_request = f'SELECT {str_cim_perf_properties} FROM {cim_perf_class}'

    # request storage via WBEM
    objects_names_cim = wbem_connection.ExecQuery('DMTF:CQL', objects_request)
    objects_perfs_cim = wbem_connection.ExecQuery('DMTF:CQL', perf_request)

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

    # unpack storage list to variables
    for device_line in device_list_file:
        device_type, device_name, device_ip = device_line.split(':')

        # connect to each storage via WBEM, get conn object
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
                # get values of object perfomance statistic for all object of each type where perfomance class is given
                if 'cim_perfomance_class' in sc_maps[storage_concept]:
                    storage_objects_perf = storage_objects_get_perf(conn,
                                                                    sc_maps[storage_concept]['cim_class'],
                                                                    sc_maps[storage_concept]['cim_property_name'],
                                                                    sc_maps[storage_concept]['cim_perfomance_class'],
                                                                    sc_maps[storage_concept]['cim_properties_perfomance'])

                    # get statistic for each storage object, form data for sending to zabbix
                    for so_name in storage_objects_perf:
                        for perf_counter_name, perf_counter_value in zip(sc_maps[storage_concept]['cim_properties_perfomance'],
                                                                         storage_objects_perf[so_name]):
                            trapper_key = (perf_counter_name + '['
                                           + storage_concept + '.' + so_name + ']')
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
