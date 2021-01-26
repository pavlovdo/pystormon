#!/usr/bin/env python3

# Python module for load parameters from main config file


def configread(conffile, section, *parameters):

    import configparser

    # read configuration file
    config = configparser.RawConfigParser()
    config.read(conffile)
    params = dict()

    # check presence of parameters in config file
    for parameter in parameters:
        try:
            params[parameter] = config.get(section, parameter)
        except configparser.NoOptionError as err:
            print(
                err, f"Please set {parameter} value in the configuration file {conffile}")

    return params
