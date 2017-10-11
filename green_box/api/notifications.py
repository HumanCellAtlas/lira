import connexion
import requests
from requests.auth import HTTPBasicAuth
import logging
import json
import subprocess
import time
from flask import make_response, current_app
from google.cloud import storage  # Imports the Google Cloud client library


def get_filename_from_gs_link(link):
    """get the filename corresponding to a google_storage link"""
    return link.split('/')[-1]


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

    # Get files from gcs # todo change to using google.cloud.storage
    subprocess.check_output(['gsutil', 'cp', wdl.wdl_link, '.'])
    subprocess.check_output(['gsutil', 'cp', wdl.wdl_default_inputs_link, '.'])
    subprocess.check_output(['gsutil', 'cp', wdl.wdl_deps_link, '.'])
    subprocess.check_output(['gsutil', 'cp', wdl.options_link, '.'])

    # get filenames from links
    wdl_file = get_filename_from_gs_link(wdl.wdl_link)
    wdl_default_inputs_file = get_filename_from_gs_link(wdl.wdl_default_inputs_link)
    wdl_deps_file = get_filename_from_gs_link(wdl.wdl_deps_link)
    options_file = get_filename_from_gs_link(wdl.options_link)

    cromwell_response = start_workflow(
        wdl_file, wdl_deps_file, 'cromwell_inputs.json',
        wdl_default_inputs_file, options_file, green_config)

    # Respond
    if cromwell_response.status_code > 201:
        logger.error(cromwell_response.text)
        return response_with_server_header(dict(result=cromwell_response.text), 500)
    logger.info(cromwell_response.json())
    return response_with_server_header(cromwell_response.json())


def response_with_server_header(body, status=200):
    response = make_response(json.dumps(body), status)
    response.headers['Server'] = 'Secondary Analysis Service'
    response.headers['Content-type'] = 'application/json'
    return response


def is_authenticated(args, token):
    if 'auth' not in args:
        return False
    elif args['auth'] != token:
        return False
    return True


def extract_uuid_version_subscription_id(msg):
    uuid = msg["match"]["bundle_uuid"]
    version = msg["match"]["bundle_version"]
    subscription_id = msg["subscription_id"]
    return uuid, version, subscription_id


def compose_inputs(workflow_name, uuid, version):
    return {workflow_name + '.bundle_uuid': uuid,
            workflow_name + '.bundle_version': '{0}'.format(version)}


def start_workflow(wdl_file, zip_file, inputs_file, inputs_file2, options_file, green_config):
    with open(wdl_file, 'rb') as wdl, open(zip_file, 'rb') as deps, \
            open(inputs_file, 'rb') as inputs, open(inputs_file2, 'rb') as inputs2, \
            open(options_file, 'rb') as options:
        files = {
          'wdlSource': wdl,
          'workflowInputs': inputs,
          'workflowInputs_2': inputs2,
          'wdlDependencies': deps,
          'workflowOptions': options
        }

        response = requests.post(
            green_config.cromwell_url, files=files,
            auth=HTTPBasicAuth(green_config.cromwell_user,
                               green_config.cromwell_password))
        return response

    
def download_gcs_blob(bucket_name, source_blob_name, destination_file_name=None):
    """Use google.cloud.storage API to download a blob from the bucket. 
        Check details: https://cloud.google.com/storage/docs/object-basics#storage-download-object-python
    """
    if not destination_file_name:  # destination_file_name is set to source_blob_name by default
        destination_file_name = source_blob_name

    storage_client = storage.Client()  # Instantiates a client
    bucket = storage_client.get_bucket(bucket_name)   # Specify the bucket to download from
    blob = bucket.blob(source_blob_name)  # Specify the blob to download

    blob.download_to_filename(destination_file_name)

    # print('Blob {} downloaded to {}.'.format(
    #     source_blob_name,
    #     destination_file_name))
    
    return 'Blob {} downloaded to {}.'.format(
            source_blob_name,
            destination_file_name)
