import sys
import logging
import os


def setup_sloth_logger(name=""):

    formatter = logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
    handler = logging.FileHandler('sloth_log.txt', mode='w')

    handler.setFormatter(formatter)
    screen_handler = logging.StreamHandler(stream=sys.stdout)
    screen_handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    logger.addHandler(screen_handler)

    return logger


sloth_log = setup_sloth_logger(os.environ.get('SLOTH_INSTANCE', ""))
