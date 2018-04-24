import logging


def get():
    """Lira's health check endpoint."""
    logger = logging.getLogger("{module_path}".format(module_path=__name__))
    logger.debug("Health check request received")
    return dict(status="healthy")
