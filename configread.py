#!/usr/bin/env python3

# Python module for load parameters from main config file

import configparser


def configread(conffile, section, *parameters):

    # read configuration file
    config = configparser.RawConfigParser()
    config.read(conffile)
    params = {}

    # check presence parameters in config file
    for parameter in parameters:
        try:
            params[parameter] = config.get(section, parameter)
        except configparser.NoOptionError as error:
            print(f'{error}. Please set {parameter} value '
                  f'in the configuration file {conffile}')

    return params
