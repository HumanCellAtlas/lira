#!/usr/bin/env python3

import requests
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
