import logging
import time
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler


def create_rotating_log(path):
    logger = logging.getLogger("Rotating Log")
    logger.setLevel(logging.INFO)

    handler = RotatingFileHandler(path, maxBytes=20, backupCount=5)
    logger.addHandler(handler)

    for i in range(10):
        logger.info("This is test log line %s" % i)
        time.sleep(1.5)


def create_timed_rotating_log(path):
    logger = logging.getLogger("Rotating Log")
    logger.setLevel(logging.INFO)

    handler = TimedRotatingFileHandler(path, when="m", interval=1, backupCount=5)
    logger.addHandler(handler)

    for i in range(6):
        logger.info("This is a test!")
        time.sleep(75)

if __name__ == "__main__":
    log_file_1 = ".\\logging_test\\rotating.log"
    create_rotating_log(log_file_1)

    # log_file_2 = ".\\logging_test\\timed_rotating.log"
    # create_timed_rotating_log(log_file_2)
