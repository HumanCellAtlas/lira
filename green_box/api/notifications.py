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

    # Get bundle uuid, version and subscription_id
    uuid, version, subscription_id = extract_uuid_version_subscription_id(body)

    # Find wdl config where the subscription_id matches the notification's subscription_id
    id_matches = [wdl for wdl in green_config.wdls if wdl.get('subscription_id') == subscription_id]
    if len(id_matches) == 0:
        return response_with_server_header(dict(error='Not Found: No wdl config found with subscription id {}'.format(subscription_id)), 404)
    elif len(id_matches) > 1:
        return response_with_server_header(dict(error='Internal Server Error: More than one wdl config found with subscription id {}'.format(subscription_id)), 500)

    # Prepare inputs
    wdl = id_matches[0]
    workflow_name = wdl.get('workflow_name')
    inputs = compose_inputs(workflow_name, uuid, version, green_config.provenance_script)
    with open('cromwell_inputs.json', 'w') as f:
        json.dump(inputs, f)

    # Start workflow
    logger.info(wdl)
    logger.info('Launching {0} workflow in Cromwell'.format(workflow_name))

    # Get files from gcs
    subprocess.check_output(['gsutil', 'cp', wdl['wdl_cloud_path'], '.'])
    subprocess.check_output(['gsutil', 'cp', wdl['default_inputs_cloud_path'], '.'])
    subprocess.check_output(['gsutil', 'cp', wdl['wdl_deps_cloud_path'], '.'])

    wdl_file = wdl['wdl_file']
    wdl_deps_file = wdl['wdl_deps_file']
    wdl_default_inputs_file = wdl['default_inputs_file']
    cromwell_response = start_workflow(wdl_file, wdl_deps_file, 'cromwell_inputs.json', wdl_default_inputs_file, green_config)

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
    if not 'auth' in args:
        return False
    elif args['auth'] != token:
        return False
    return True

def extract_uuid_version_subscription_id(msg):
    uuid = msg["match"]["bundle_uuid"]
    version = msg["match"]["bundle_version"]
    subscription_id = msg["subscription_id"]
    return uuid, version, subscription_id

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
