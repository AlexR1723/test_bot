# coding: utf-8

import logging
import logging.handlers


def create_logger(filename, logger_name='logger', level=logging.INFO):
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)

    #formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(name)s (%(module)s) | %(message)s', '%Y-%m-%d %H:%M:%S')
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(module)s | %(message)s', '%d.%m.%y %H:%M:%S')

    file_handler = logging.handlers.RotatingFileHandler(filename, maxBytes=10 * 1024 * 1024, backupCount=50)
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger

"""
log levels:
CRITICAL - 50
ERROR - 40
WARNING - 30
INFO - 20
DEBUG - 10
NOTSET - 0
"""