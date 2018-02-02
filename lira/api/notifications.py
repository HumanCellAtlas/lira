import connexion
import logging
import json
import time
from flask import current_app
from cromwell_tools import cromwell_tools
from lira import lira_utils

logger = logging.getLogger("Lira | {module_path}".format(module_path=__name__))


def post(body):
    """Process notification and launch workflow in Cromwell"""

    # Check authentication
    lira_config = current_app.config
    if not lira_utils.is_authenticated(connexion.request.args, lira_config.notification_token):
        time.sleep(1)
        return lira_utils.response_with_server_header(dict(error='Unauthorized'), 401)

    logger.info("Notification received")
    logger.debug("Received notification body: {notification}".format(notification=body))

    # Get bundle uuid, version and subscription_id
    uuid, version, subscription_id = lira_utils.extract_uuid_version_subscription_id(body)

    # Find wdl config where the subscription_id matches the notification's subscription_id
    id_matches = [wdl for wdl in lira_config.wdls if wdl.subscription_id == subscription_id]
    if len(id_matches) == 0:
        return lira_utils.response_with_server_header(
            dict(error='Not Found: No wdl config found with subscription id {}'
                       ''.format(subscription_id)), 404)
    wdl_config = id_matches[0]
    logger.debug("Matched WDL config: {wdl}".format(wdl=wdl_config))
    logger.info("Preparing to launch {workflow_name} workflow in Cromwell".format(workflow_name=wdl_config.workflow_name))

    # Prepare inputs
    inputs = lira_utils.compose_inputs(wdl_config.workflow_name, uuid, version, lira_config.env)
    cromwell_inputs_file = json.dumps(inputs)

    cromwell_submission = current_app.prepare_submission(wdl_config, lira_config.submit_wdl)
    logger.info(current_app.prepare_submission.cache_info())


    dry_run = getattr(lira_config, 'dry_run', False)
    if dry_run:
        logger.warning('Not launching workflow because Lira is in dry_run mode')
        response_json = {
            'id': 'fake_id',
            'status': 'fake_status'
        }
        status_code = 201
    else:
        cromwell_response = cromwell_tools.start_workflow(
            wdl_file=cromwell_submission.wdl_file,
            zip_file=cromwell_submission.wdl_deps_file,
            inputs_file=cromwell_inputs_file,
            inputs_file2=cromwell_submission.wdl_static_inputs_file,
            options_file=cromwell_submission.options_file,
            url=lira_config.cromwell_url,
            user=lira_config.cromwell_user,
            password=lira_config.cromwell_password
        )
        if cromwell_response.status_code > 201:
            logger.error("HTTP error content: {content}".format(content=cromwell_response.text))
            response_json = dict(result=cromwell_response.text)
            status_code = 500
        else:
            response_json = cromwell_response.json()
            logger.info("Cromwell response: {0} {1}".format(response_json, cromwell_response.status_code))
            status_code = 201

    return lira_utils.response_with_server_header(response_json, status_code)


def create_prepare_submission_function(cache_wdls):
    """Returns decorated prepare_submission function. Decorator is determined as follows:
    Python 2: Always decorate with noop_lru_cache, since functools.lru_cache is not available in 2.
    Python 3: Use functools.lru_cache if cache_wdls is true, otherwise use noop_lru_cache."""

    # Use noop_lru_cache unless cache_wdls is true and functools.lru_cache is available
    lru_cache = lira_utils.noop_lru_cache
    if not cache_wdls:
        logger.info('Not caching wdls because Lira is configured with cache_wdls false')
    else:
        try:
            from functools import lru_cache
        except ImportError:
            logger.info('Not caching wdls because functools.lru_cache is not available in Python 2.')

    @lru_cache(maxsize=None)
    # Setting maxsize to None here means each unique call to prepare_submission (defined by parameters used)
    # will be added to the cache without evicting any other items. Additional non-unique calls
    # (parameters identical to a previous call) will read from the cache instead of actually
    # calling this function. This means that the function will be called no more than once for
    # each wdl config, but we can have arbitrarily many wdl configs without running out of space
    # in the cache.
    def prepare_submission(wdl_config, submit_wdl):
        """Load into memory all static data needed for submitting a workflow to Cromwell"""

        # Read files into memory
        wdl_file = cromwell_tools.download(wdl_config.wdl_link)
        wdl_static_inputs_file = cromwell_tools.download(wdl_config.wdl_static_inputs_link)
        options_file = cromwell_tools.download(wdl_config.options_link)

        # Create zip of analysis and submit wdls
        url_to_contents = cromwell_tools.download_to_map(wdl_config.analysis_wdls + [submit_wdl])
        wdl_deps_file = cromwell_tools.make_zip_in_memory(url_to_contents)

        return CromwellSubmission(wdl_file, wdl_static_inputs_file, options_file, wdl_deps_file)

    return prepare_submission


class CromwellSubmission(object):
    """Holds static data needed for submitting a workflow to Cromwell, including
    the top level wdl file, the static inputs json file, the options file,
    and the dependencies zip file.
    """

    def __init__(self, wdl_file, wdl_static_inputs_file=None, options_file=None, wdl_deps_file=None):
        self.wdl_file = wdl_file
        self.wdl_static_inputs_file = wdl_static_inputs_file
        self.options_file = options_file
        self.wdl_deps_file = wdl_deps_file
