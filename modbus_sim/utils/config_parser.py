"""
Copyright (c) 2016 Riptide IO, Inc. All Rights Reserved.

"""
from __future__ import absolute_import, unicode_literals
from ConfigParser import ConfigParser
import yaml


class YamlConfigParser(object):

    @staticmethod
    def read(config_file):
        config = dict()
        with open(config_file) as conffile:
            config = yaml.load(conffile.read())
        return config

    @staticmethod
    def write(content, config_file):
        with open(config_file, "w+") as conffile:
            yaml.dump(content, conffile, default_flow_style=False)


def build_config():
    config = ConfigParser()
    config.add_section('Modbus Tcp')
    config.add_section('Modbus Protocol')
    config.add_section('Modbus Serial')
    config.set('Modbus Tcp', "ip", '127.0.0.1')
    config.set('Modbus Protocol', "block start", "0")
    config.set('Modbus Protocol', "block size", "100")
    config.set('Modbus Protocol', "bin min", "0")
    config.set('Modbus Protocol', "bin max", "1")
    config.set('Modbus Protocol', "reg min", "0")
    config.set('Modbus Protocol', "reg max", "65535")
    config.set('Modbus Serial', "baudrate", "9600")
    config.set('Modbus Serial', "bytesize", "8")
    config.set('Modbus Serial', "parity", 'N')
    config.set('Modbus Serial', "stopbits", "1")
    config.set('Modbus Serial', "xonxoff", "0")
    config.set('Modbus Serial', "rtscts", "0")
    config.set('Modbus Serial', "dsrdtr", "0")
    config.set('Modbus Serial', "writetimeout", "2")
    config.set('Modbus Serial', "timeout", "2")

    config.add_section('Logging')
    # config.set('Logging', "log file", os.path.join(self.user_data_dir,
    #                                                'modbus.log'))

    config.set('Logging', "logging", "1")
    config.set('Logging', "console logging", "1")
    config.set('Logging', "console log level", "DEBUG")
    config.set('Logging', "file log level", "DEBUG")
    config.set('Logging', "file logging", "1")

    config.add_section('Simulation')
    config.set('Simulation', 'time interval', "1")
    return config

