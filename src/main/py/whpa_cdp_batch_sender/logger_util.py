import logging
import sys


_log_format = '{asctime} [{threadName}] [{levelname}] [{name}] - {message}'

def get_file_handler(filename):
    file_handler = logging.FileHandler(filename)
    file_handler.setLevel(logging.WARNING)
    file_handler.setFormatter(logging.Formatter(_log_format, style='{'))
    return file_handler


def get_sysout_stream_handler(stream):
    stream_handler = logging.StreamHandler(stream)
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(logging.Formatter(_log_format, style='{'))
    return stream_handler


def get_logger(name, stream=sys.stdout, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(get_sysout_stream_handler(stream))
    return logger