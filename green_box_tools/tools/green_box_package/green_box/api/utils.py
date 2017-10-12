#!/usr/bin/env python3

import requests
import json
import logging
from requests.auth import HTTPBasicAuth
from flask import make_response
from google.cloud import storage  # Imports the Google Cloud client library


def get_filename_from_gs_link(link):
    """Get the filename corresponding to a google_storage link."""
    return link.split('/')[-1]


def get_bucketname_from_gs_link(link):
    """Get the bucketname corresponding to a google_storage link."""
    return link.split('/')[-2]


def response_with_server_header(body, status=200):
    """Add information of server to hearder."""
    response = make_response(json.dumps(body), status)
    response.headers['Server'] = 'Secondary Analysis Service'
    response.headers['Content-type'] = 'application/json'
    return response


def is_authenticated(args, token):
    """Check if is authenticated."""
    if 'auth' not in args:
        return False
    elif args['auth'] != token:
        return False
    return True


def extract_uuid_version_subscription_id(msg):
    """Prepare inputs | Extract uuid, version, subscription_id from messeage."""
    uuid = msg["match"]["bundle_uuid"]
    version = msg["match"]["bundle_version"]
    subscription_id = msg["subscription_id"]
    return uuid, version, subscription_id


def compose_inputs(workflow_name, uuid, version):
    """Prepare inputs | Compose workflow_name, uuid, version to a dictionary."""
    return {workflow_name + '.bundle_uuid': uuid,
            workflow_name + '.bundle_version': '{0}'.format(version)}


def start_workflow(wdl_file, zip_file, inputs_file, inputs_file2, options_file, green_config):
    """Use post method to call Cromwell API and get response."""
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


def download_gcs_blob(authenticated_gcs_client, bucket_name, source_blob_name, destination_file_path='./', destination_file_name=None):
    """Use google.cloud.storage API to download a blob from the bucket."""
    if not destination_file_name:  # destination_file_name is set to source_blob_name by default
        destination_file_name = source_blob_name
    destination_file_name = validate_path(destination_file_path) + str(source_blob_name)

    try:
        storage_client = authenticated_gcs_client  # pass the client as a parameter here
        bucket = storage_client.get_bucket(bucket_name)
        blob = bucket.blob(source_blob_name)
        blob.download_to_filename(destination_file_name)
        logging.info('Blob {} downloaded to {}.'.format(source_blob_name, destination_file_name))
    except:
        logging.debug(
            'An error occurred during downloading blob {} from Google Cloud Storage'.format(source_blob_name))


def validate_path(filepath):
    """Validate if the filepath ends with slash, if not, add the slash to the end."""
    if not str(filepath).endswith('/'):
        return str(filepath)+'/'
    return str(filepath)

