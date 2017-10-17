import connexion
import logging
import json
import time
from flask import current_app
from listener_utils import *


def post(body):
    # Check authentication
    logger = logging.getLogger('green-box')
    green_config = current_app.config
    if not is_authenticated(connexion.request.args, green_config.notification_token):
        time.sleep(1)
        return response_with_server_header(dict(error='Unauthorized'), 401)

    logger.info("Notification received")
    logger.info(body)

    # Get bundle uuid, version and subscription_id
    uuid, version, subscription_id = extract_uuid_version_subscription_id(body)

    # Find wdl config where the subscription_id matches the notification's subscription_id
    id_matches = [wdl for wdl in green_config.wdls if wdl.subscription_id == subscription_id]
    if len(id_matches) == 0:
        return response_with_server_header(
            dict(error='Not Found: No wdl config found with subscription id {}'
                       ''.format(subscription_id)), 404)
    wdl = id_matches[0]

    # Prepare inputs
    inputs = compose_inputs(wdl.workflow_name, uuid, version)
    with open('cromwell_inputs.json', 'w') as f:
        json.dump(inputs, f)

    # Start workflow
    logger.info(wdl)
    logger.info('Launching {0} workflow in Cromwell'.format(wdl.workflow_name))

    # ToDo: Parse bucket at initialization time in config class, throw an error if malformed.
    bucket_name, _ = parse_bucket_blob_from_gs_link(wdl.wdl_link)

    # get filenames from links
    wdl_file = get_filename_from_gs_link(wdl.wdl_link)
    wdl_default_inputs_file = get_filename_from_gs_link(wdl.wdl_default_inputs_link)
    wdl_deps_file = get_filename_from_gs_link(wdl.wdl_deps_link)
    options_file = get_filename_from_gs_link(wdl.options_link)

    # Get files from gcs
    # subprocess.check_output(['gsutil', 'cp', wdl.wdl_link, '.'])
    # subprocess.check_output(['gsutil', 'cp', wdl.wdl_default_inputs_link, '.'])
    # subprocess.check_output(['gsutil', 'cp', wdl.wdl_deps_link, '.'])
    # subprocess.check_output(['gsutil', 'cp', wdl.options_link, '.'])

    storage_client = current_app.client
    download_gcs_blob(storage_client, bucket_name, wdl_file)
    download_gcs_blob(storage_client, bucket_name, wdl_default_inputs_file)
    ldownload_gcs_blob(storage_client, bucket_name, wdl_deps_file)
    download_gcs_blob(storage_client, bucket_name, options_file)
    
    cromwell_response = start_workflow(
        wdl_file, wdl_deps_file, 'cromwell_inputs.json',
        wdl_default_inputs_file, options_file, green_config)

    # Respond
    if cromwell_response.status_code > 201:
        logger.error(cromwell_response.text)
        return response_with_server_header(dict(result=cromwell_response.text), 500)
    logger.info(cromwell_response.json())
    return response_with_server_header(cromwell_response.json())
