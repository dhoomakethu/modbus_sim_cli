# Modbus TCP/RTU device simulation tool

# Usage

```
$ modbus_simulator -h
usage: Modbus Simulator [-h] -c str
                        [--console-log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                        [--enable-file-logging]
                        [--file-log-level {debug,info,warning,error,critical}]
                        [--log-file LOG_FILE] [--version] [-D]

- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

modbus_simu
~~~~~~~~~~
```
Modbus simulator CLI version based on Modbus tk

optional arguments:
  -h, --help            show this help message and exit
  -c (str), --simu-config (str)
                        Default configuration file to be used for modbus simulation script
  --console-log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Monitor console log level, overides value from configuration file
  --enable-file-logging
                        Enable file logging
  --file-log-level {debug,info,warning,error,critical}
                        Simulator file log level, overides value from configuration file
  --log-file LOG_FILE   Default simulation log file
  --version             show program's version number and exit
  -D, --debug           Turn on to enable tracing

- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
```
```

# To run
modbus_simulator  -c <PATH to config file>

# sample simulation config
[conf.yml](configs/conf.yml)


## Copyright (c) 2016 Riptide IO, Inc. All Rights Reserved.