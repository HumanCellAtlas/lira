import connexion
import logging
import json
import time
from flask import current_app
from pipeline_tools import gcs_utils
from cromwell_tools import cromwell_tools
import utils as listener_utils


def post(body):
    # Check authentication
    logger = logging.getLogger('green-box')
    green_config = current_app.config

    if not listener_utils.is_authenticated(connexion.request.args, green_config.notification_token):
        time.sleep(1)
        return listener_utils.response_with_server_header(dict(error='Unauthorized'), 401)

    logger.info("Notification received")
    logger.info(body)

    # Get bundle uuid, version and subscription_id
    uuid, version, subscription_id = listener_utils.extract_uuid_version_subscription_id(body)

    # Find wdl config where the subscription_id matches the notification's subscription_id
    id_matches = [wdl for wdl in green_config.wdls if wdl.subscription_id == subscription_id]
    if len(id_matches) == 0:
        return listener_utils.response_with_server_header(
            dict(error='Not Found: No wdl config found with subscription id {}'
                       ''.format(subscription_id)), 404)
    wdl = id_matches[0]

    # Prepare inputs
    inputs = listener_utils.compose_inputs(wdl.workflow_name, uuid, version)
    with open('cromwell_inputs.json', 'w') as f:
        json.dump(inputs, f)

    # Start workflow
    logger.info(wdl)
    logger.info('Launching {0} workflow in Cromwell'.format(wdl.workflow_name))

    # TODO: Parse bucket at initialization time in config class, throw an error if malformed.
    # get filenames from links
    bucket_name, wdl_file = gcs_utils.parse_bucket_blob_from_gs_link(wdl.wdl_link)
    _, wdl_default_inputs_file = gcs_utils.parse_bucket_blob_from_gs_link(wdl.wdl_default_inputs_link)
    _, wdl_deps_file = gcs_utils.parse_bucket_blob_from_gs_link(wdl.wdl_deps_link)
    _, options_file = gcs_utils.parse_bucket_blob_from_gs_link(wdl.options_link)

    # Get files from gcs and store in Bytes Buffer
    gcs_client = current_app.gcs_client
    wdl_file = gcs_utils.download_gcs_blob(gcs_client, bucket_name, wdl_file)
    wdl_default_inputs_file = gcs_utils.download_gcs_blob(gcs_client, bucket_name, wdl_default_inputs_file)
    wdl_deps_file = gcs_utils.download_gcs_blob(gcs_client, bucket_name, wdl_deps_file)
    options_file = gcs_utils.download_gcs_blob(gcs_client, bucket_name, options_file)

    with open('cromwell_inputs.json') as cromwell_inputs_file:
        cromwell_response = cromwell_tools.start_workflow(
            wdl_file, wdl_deps_file, cromwell_inputs_file,
            wdl_default_inputs_file, options_file, green_config.cromwell_url,
            green_config.cromwell_user, green_config.cromwell_password)

    # Respond
    if cromwell_response.status_code > 201:
        logger.error(cromwell_response.text)
        return listener_utils.response_with_server_header(dict(result=cromwell_response.text), 500)
    logger.info(cromwell_response.json())
    return listener_utils.response_with_server_header(cromwell_response.json())
