import logging


def get():
    logger = logging.getLogger("Lira | {module_path}".format(module_path=__name__))
    logger.info("Health check request received")
    return dict(status="healthy")
