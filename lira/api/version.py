import logging
from flask import current_app
import cromwell_tools
from lira import lira_utils


def get_version():
    """Gather and return Lira's and all its dependencies' versions."""
    logger = logging.getLogger("{module_path}".format(module_path=__name__))
    logger.debug("Version request received")

    lira_config = current_app.config

    workflow_info = {
        wdl.workflow_name: {
            'version': wdl.workflow_version,
            'subscription_id': wdl.subscription_id
        } for wdl in lira_config.wdls
    }

    try:
        submit_wdl_version = lira_utils.parse_github_resource_url(lira_config.get('submit_wdl')).version or "Unknown"
    except ValueError:
        submit_wdl_version = "Unknown"

    version_response = {
        "launch_time": current_app.launch_time,
        "config_version": current_app.config_name,
        "Lira_version": lira_config.get('version'),
        "Cromwell_tools_version": cromwell_tools.__version__ or "Unknown",
        "submit_wdl_version": submit_wdl_version,
        "run_mode": "dry_run" if lira_config.get('dry_run') else "live_run",
        "workflow_info": workflow_info
    }

    return version_response
