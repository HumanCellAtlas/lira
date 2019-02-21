import logging


def get():
    """Lira's health check endpoint."""
    logger = logging.getLogger("{module_path}".format(module_path=__name__))
    logger.debug("Health check request received")
    # TODO: make this endpoint more useful(check the Cromwell status as well) and comply with the API definition
    return dict(status="healthy")
