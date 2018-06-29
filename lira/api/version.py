import logging
from flask import current_app
import cromwell_tools
from lira import lira_utils


def get_version():
    """Collect and return Lira's and all its dependencies' versions."""
    logger = logging.getLogger('{module_path}'.format(module_path=__name__))
    logger.debug('Version request received')

    lira_config = current_app.config

    try:
        submit_wdl_version = lira_utils.parse_github_resource_url(lira_config.get('submit_wdl')).version or 'Unknown'
    except ValueError:
        submit_wdl_version = 'Unknown'

    workflow_info = {
        wdl.workflow_name: {
            'version': wdl.workflow_version,
            'subscription_id': wdl.subscription_id
        } for wdl in lira_config.wdls
    }

    version_info = {
        'cromwell_tools_version': cromwell_tools.__version__ or 'Unknown',
        'lira_version': lira_config.version,
        'submit_wdl_version': submit_wdl_version
    }

    settings_info = {
        'cromwell_url': lira_config.get('cromwell_url'),
        'data_store_url': lira_config.get('dss_url'),
        'ingest_url': lira_config.get('ingest_url'),
        'launch_time': current_app.launch_time,
        'max_cromwell_retries': lira_config.get('max_cromwell_retries'),
        'run_mode': 'dry_run' if lira_config.get('dry_run') else 'live_run',
        'stale_notification_timeout': lira_config.get('stale_notification_timeout'),
        'use_caas': lira_config.get('use_caas')
    }

    version_response = {
        "settings_info": settings_info,
        "version_info": version_info,
        "workflow_info": workflow_info
    }

    return version_response
