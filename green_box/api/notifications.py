import connexion
import requests
from requests.auth import HTTPBasicAuth
import logging
import json
import subprocess
import time
from collections import namedtuple, OrderedDict
from flask import make_response, current_app

def post(body):
    # Check authentication
    logger = logging.getLogger('green-box')
    ordered_config = OrderedDict(current_app.config)
    Config = namedtuple('config', ordered_config.keys())
    green_config = Config(*ordered_config.values())
    if not is_authenticated(connexion.request.args, green_config.notification_token):
        time.sleep(1)
        return response_with_server_header(dict(error='Unauthorized'), 401)

    logger.info("Notification received")
    logger.info(body)

    # Get bundle uuid and version
    uuid, version = extract_uuid_version(body)

    # Prepare inputs
    inputs = compose_inputs(green_config.workflow_name, uuid, version, green_config.provenance_script)
    with open('cromwell_inputs.json', 'w') as f:
        json.dump(inputs, f)

    # Start workflow
    logger.info('Launching {0} workflow in Cromwell'.format(green_config.workflow_name))
    result = subprocess.check_output(['gsutil', 'cp', green_config.wdl_cloud_path, '.'])
    result = subprocess.check_output(['gsutil', 'cp', green_config.wdl_deps_cloud_path, '.'])
    result = subprocess.check_output(['gsutil', 'cp', green_config.default_inputs_cloud_path, '.'])
    cromwell_response = start_workflow(green_config.wdl_file, green_config.wdl_deps_file, 'cromwell_inputs.json', green_config.default_inputs_file, green_config)

    # Respond
    if cromwell_response.status_code > 201:
        logger.error(response.text)
        return response_with_server_header(dict(result=cromwell_response.text), 500)
    logger.info(cromwell_response.json())
    return response_with_server_header(cromwell_response.json())

def response_with_server_header(body, status=200):
    response = make_response(json.dumps(body), status)
    response.headers['Server'] = 'Secondary Analysis Service'
    response.headers['Content-type'] = 'application/json'
    return response

def is_authenticated(args, token):
    if not 'auth' in args:
        return False
    elif args['auth'] != token:
        return False
    return True

def extract_uuid_version(msg):
    uuid = msg["match"]["bundle_uuid"]
    version = msg["match"]["bundle_version"]
    return uuid, version

def compose_inputs(workflow_name, uuid, version, provenance_script):
    inputs = {}
    inputs[workflow_name + '.bundle_uuid'] = uuid
    inputs[workflow_name + '.bundle_version'] = '{0}'.format(version)
    inputs[workflow_name + '.provenance_script'] = provenance_script
    return inputs

def start_workflow(wdl_file, zip_file, inputs_file, inputs_file2, green_config):
    with open(wdl_file, 'rb') as wdl, open(zip_file, 'rb') as deps, open(inputs_file, 'rb') as inputs, open(inputs_file2, 'rb') as inputs2:
        files = {
          'wdlSource': wdl,
          'workflowInputs': inputs,
          'workflowInputs_2': inputs2,
          'wdlDependencies': deps
        }
        response = requests.post(green_config.cromwell_url, files=files, auth=HTTPBasicAuth(green_config.cromwell_user, green_config.cromwell_password))
        return response

