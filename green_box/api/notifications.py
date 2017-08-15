import connexion
import requests
from requests.auth import HTTPBasicAuth
import logging
import json
import subprocess
import green_config
import time
import flask

def post(body):
    # Check authentication
    if not is_authenticated(connexion.request.args, green_config.notification_token):
        time.sleep(1)
        return response_with_server_header(dict(error='Unauthorized'), 401)

    logger = logging.getLogger('green-box')
    logger.info("Notification received")
    logger.info(body)

    # Get bundle uuid and version
    uuid, version = extract_uuid_version(body)

    # Prepare inputs
    inputs = compose_inputs(uuid, version, green_config.provenance_script)
    with open('cromwell_inputs.json', 'w') as f:
        json.dump(inputs, f)

    # Start workflow
    logger.info("Launching smartseq2 workflow in Cromwell")
    result = subprocess.check_output(['gsutil', 'cp', green_config.mock_smartseq2_wdl, '.'])
    cromwell_response = start_workflow('mock_smartseq2.wdl', 'cromwell_inputs.json')

    # Respond
    if cromwell_response.status_code > 201:
        logger.error(response.text)
        return response_with_server_header(dict(result=cromwell_response.text), 500)
    logger.info(cromwell_response.json())
    return response_with_server_header(cromwell_response.json())

def response_with_server_header(body, status=200):
    response = flask.make_response(json.dumps(body), status)
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

def compose_inputs(uuid, version, provenance_script):
    inputs = {}
    inputs['mock_smartseq2.bundle_uuid'] = uuid
    inputs['mock_smartseq2.bundle_version'] = '"{0}"'.format(version)
    inputs['mock_smartseq2.provenance_script'] = provenance_script
    return inputs

def start_workflow(wdl, inputs):
    with open('mock_smartseq2.wdl', 'rb') as wdl, open('cromwell_inputs.json', 'rb') as inputs:
        files = {
          'wdlSource': wdl,
          'workflowInputs': inputs
        }
        response = requests.post(green_config.cromwell_url, files=files, auth=HTTPBasicAuth(green_config.cromwell_user, green_config.cromwell_password))
        return response

