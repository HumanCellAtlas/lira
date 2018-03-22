import connexion
import logging
import json
import time
from flask import current_app
from cromwell_tools import cromwell_tools
from lira import lira_utils

logger = logging.getLogger("{module_path}".format(module_path=__name__))


def post(body):
    """Process notification and launch workflow in Cromwell"""

    # Check authentication
    lira_config = current_app.config
    if not lira_utils.is_authenticated(connexion.request.args, lira_config.notification_token):
        time.sleep(1)
        return lira_utils.response_with_server_header(dict(error='Unauthorized'), 401)

    logger.info("Notification received")
    logger.info("Received notification body: {notification}".format(notification=body))

    # Get bundle uuid, version and subscription_id
    uuid, version, subscription_id = lira_utils.extract_uuid_version_subscription_id(body)

    # Find wdl config where the subscription_id matches the notification's subscription_id
    id_matches = [wdl for wdl in lira_config.wdls if wdl.subscription_id == subscription_id]
    if len(id_matches) == 0:
        return lira_utils.response_with_server_header(
            dict(error='Not Found: No wdl config found with subscription id {}'
                       ''.format(subscription_id)), 404)
    wdl_config = id_matches[0]
    logger.info("Matched WDL config: {wdl}".format(wdl=wdl_config))
    logger.info("Preparing to launch {workflow_name} workflow in Cromwell".format(workflow_name=wdl_config.workflow_name))

    # Prepare inputs
    inputs = lira_utils.compose_inputs(wdl_config.workflow_name, uuid, version, lira_config.env)
    cromwell_inputs_file = json.dumps(inputs)

    # Prepare labels
    cromwell_labels = json.dumps(body.get('labels'))
    if cromwell_labels:
        logger.info("Will add labels: {labels} to the workflow after syntax validation".format(labels=cromwell_labels))

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
            zip_file=cromwell_tools.make_zip_in_memory(cromwell_submission.wdl_deps_dict),
            inputs_file=cromwell_inputs_file,
            inputs_file2=cromwell_submission.wdl_static_inputs_file,
            options_file=cromwell_submission.options_file,
            url=lira_config.cromwell_url,
            user=lira_config.cromwell_user,
            password=lira_config.cromwell_password,
            label=cromwell_labels
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
