#!/usr/bin/env python

import argparse
import json
from datetime import datetime
from datetime import timedelta
import requests
import subprocess
import time

failed_statuses = ['Failed', 'Aborted', 'Aborting']

def run(args):
    cromwell_user, cromwell_pw = extract_credentials(args.secrets_file)
    workflow_ids = args.workflow_ids.split(',')
    workflow_names = args.workflow_names.split(',')
    start = datetime.now()
    timeout = timedelta(minutes=int(args.timeout_minutes))
    while True:
        if datetime.now() - start > timeout:
            msg = 'Unfinished workflows after {0} minutes.'
            raise Exception(msg.format(timeout))
        statuses = get_statuses(workflow_names, workflow_ids, args.cromwell_url, cromwell_user, cromwell_pw)
        all_succeeded = True
        for i, status in enumerate(statuses):
            if status in failed_statuses:
                raise Exception('Stopping because {0} workflow {1} {2}'.format(workflow_names[i], workflow_ids[i], status))
            elif status != 'Succeeded':
                all_succeeded = False
        if all_succeeded:
            print('All workflows succeeded!')
            break
        else:
            time.sleep(10)

def get_statuses(names, ids, cromwell_url, user, pw):
    statuses = []
    for i, name in enumerate(names):
        id = ids[i]
        full_url = cromwell_url + '/api/workflows/v1/{0}/status'.format(id)
        response = requests.get(full_url, auth=requests.auth.HTTPBasicAuth(user, pw))
        if response.status_code != 200:
            msg = 'Could not get status for {0} workflow {1}. Cromwell at {2} returned status {3}'
            print(msg.format(name, id, cromwell_url, status_code))
            statuses.append('Unknown')
        else:
            response_json = response.json()
            status = response_json['status']
            statuses.append(status)
            print('{0} workflow {1}: {2}'.format(name, id, status))
    return statuses

def extract_credentials(secrets_file):
    with open(secrets_file) as f:
        secrets = json.load(f)
        return secrets['cromwell_user'], secrets['cromwell_password']

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--workflow_ids')
    parser.add_argument('--workflow_names')
    parser.add_argument('--cromwell_url')
    parser.add_argument('--secrets_file')
    parser.add_argument('--timeout_minutes')
    args = parser.parse_args()
    run(args)
