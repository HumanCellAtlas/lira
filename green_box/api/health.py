import logging


def get():
    logger = logging.getLogger('green-box')
    logger.info("Health check request received")
    return dict(status="healthy")
