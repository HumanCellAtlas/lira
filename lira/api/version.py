import logging
from flask import current_app
import cromwell_tools
from lira import lira_utils


def get_version() -> dict:
    """Collect and return Lira's and all its dependencies' versions."""
    logger = logging.getLogger('{module_path}'.format(module_path=__name__))
    logger.debug('Version request received')

    lira_config = current_app.config

    try:
        adapter_pipelines_version = (
            lira_utils.parse_github_resource_url(lira_config.get('submit_wdl')).version
            or 'Unknown'
        )
    except ValueError:
        adapter_pipelines_version = 'Unknown'

    workflow_info = {
        wdl.workflow_name: {
            'version': wdl.workflow_version,
            'subscription_id': wdl.subscription_id,
            'query': f'https://github.com/HumanCellAtlas/lira/tree/{lira_config.version}/subscription/elasticsearch_queries',
        }
        for wdl in lira_config.wdls
    }

    version_info = {
        'cromwell_tools_version': cromwell_tools.__version__ or 'Unknown',
        'lira_version': lira_config.version,
        'adapter_pipelines_version': adapter_pipelines_version,
    }

    settings_info = {
        'cache_wdls': lira_config.cache_wdls,
        'cromwell_url': lira_config.get('cromwell_url'),
        'data_store_url': lira_config.get('dss_url'),
        'ingest_url': lira_config.get('ingest_url'),
        'launch_time': current_app.launch_time,
        'max_cromwell_retries': int(lira_config.get('max_cromwell_retries')),
        'run_mode': 'dry_run' if lira_config.get('dry_run') else 'live_run',
        'submit_and_hold_workflows': lira_config.submit_and_hold,
        'use_caas': lira_config.get('use_caas'),
    }

    version_response = {
        "settings_info": settings_info,
        "version_info": version_info,
        "workflow_info": workflow_info,
    }

    return version_response
