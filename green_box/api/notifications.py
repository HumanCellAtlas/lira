import connexion
import requests
from requests.auth import HTTPBasicAuth
import logging
import json
import subprocess
import green_config

def post(body):
    if not 'auth' in connexion.request.headers:
        return dict()
    elif connexion.request.headers['auth'] != green_config.notification_token:
        return dict()
    logger = logging.getLogger('green-box')
    logger.info("Notification received")
    logger.info(body)
    notification = body
    uuid = notification["match"]["bundle_uuid"]
    version = notification["match"]["bundle_version"]

    # Prepare inputs
    inputs = {}
    inputs['mock_smartseq2.bundle_uuid'] = uuid
    inputs['mock_smartseq2.bundle_version'] = '"{0}"'.format(version)
    inputs['mock_smartseq2.provenance_script'] = 'gs://broad-dsde-mint-dev-teststorage/mock_provenance.py'
    with open('cromwell_inputs.json', 'w') as f:
        json.dump(inputs, f)

    # Run workflow
    logger.info("Launching smartseq2 workflow in Cromwell")
    with open('green_config.txt') as f:
        cromwell_url = f.readline().strip()
    result = subprocess.check_output(['gsutil', 'cp', 'gs://broad-dsde-mint-dev-teststorage/mock_smartseq2.wdl', '.'])
    with open('mock_smartseq2.wdl', 'rb') as wdl, open('cromwell_inputs.json', 'rb') as inputs:
        files = {
          'wdlSource': wdl,
          'workflowInputs': inputs
        }
        response = requests.post(cromwell_url, files=files, auth=HTTPBasicAuth(green_config.user, green_config.password))
        logger.info(response.json())

    return dict(result=response.text)
