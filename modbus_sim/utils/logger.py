"""
Copyright (c) 2016 Riptide IO, Inc. All Rights Reserved.

"""
from __future__ import absolute_import, unicode_literals
import logging
import os
try:
    import coloredlogs
    USE_BASIC_LOGGER = False
except ImportError:
    USE_BASIC_LOGGER = True
from modbus_sim.utils.common import path, make_dir


FIELD_STYLES = dict(
    asctime=dict(color='green'),
    hostname=dict(color='magenta'),
    levelname=dict(color='blue', bold=False),
    programname=dict(color='cyan'),
    name=dict(color='blue'),
    module=dict(color='cyan'),
    lineno=dict(color='magenta')
)

LEVEL_STYLES = {
    'DEBUG': {"color": "blue"},
    'INFO': {"color": "green"},
    'WARNING': {"color": "yellow"},
    'ERROR': {"color": "red"},
    'CRITICAL': {"color": 'red'}
}

LEVEL_FORMATS = {
    # "INFO": {'fmt': "%(asctime)s - %(levelname)s - "
    #                 "%(module)s - %(message)s"},
    "INFO": {'fmt': "%(asctime)s -  %(name)s -"
                    " %(levelname)s - %(message)s"},
    "DEBUG": {'fmt': "%(asctime)s -  %(name)s - %(levelname)s - "
                     "%(module)s::%(funcName)s @ %(lineno)d - %(message)s"
              },
    "WARNING": {'fmt': "%(message)s"}
}

LOGGERS = {}


def set_logger(logger_name,
               console_loglevel,
               filelogging=False,
               file_loglevel="WARNING",
               logfile=None,
               logfmt=None):


    global LOGGERS
    log = logging.getLogger(logger_name)
    # fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s\n%(detail)s'
    fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    fmt = fmt if not logfmt else logfmt
    log.propagate = False
    formatter = logging.Formatter(fmt)
    if USE_BASIC_LOGGER:
        log.setLevel(console_loglevel.upper())
        ch = logging.StreamHandler()
        ch.setLevel(console_loglevel.upper())

        ch.setFormatter(formatter)
        log.addHandler(ch)
    else:
        # coloredlogs.install(level=loglevel.upper(), logger=log)
        coloredlogs.install(
            level=console_loglevel.upper(),
            field_styles=FIELD_STYLES,
            level_styles=LEVEL_STYLES,
            overridefmt=LEVEL_FORMATS,
            logger=log,
            fmt=fmt
        )
        log.setLevel(console_loglevel.upper())
    if filelogging:
        func_log = path(logfile)
        make_dir(os.path.dirname(func_log))
        fh = logging.FileHandler(func_log)
        fh.setFormatter(formatter)
        fh.setLevel(file_loglevel)
        log.addHandler(fh)

    log.addFilter(CustomFilter())
    LOGGERS[logger_name] = log
    return log


def get_logger(logger_name, log_level="WARNING", logfmt=None):
    logger = LOGGERS.get(logger_name, None)
    if not logger:
        logger = set_logger(logger_name, log_level, logfmt=logfmt)
    return logger


class CustomFilter(logging.Filter):
    def filter(self, record):
        if hasattr(record, 'detail') and len(record.detail) > 0:
            record.msg = record.msg + '\n\t' + record.detail
        return super(CustomFilter, self).filter(record)

