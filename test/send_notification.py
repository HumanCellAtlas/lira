#!/usr/bin/env python

import argparse
import json
import requests

def run(args):
    with open(args.notification) as f:
        notification = json.load(f)

    with open(args.secrets_file) as f:
        secrets = json.load(f)
        token = secrets['notification_token']
        full_url = args.lira_url + '?auth={0}'.format(token)

    response = requests.post(full_url, json=notification)    
    if response.status_code == 200:
        response_json = response.json()
        workflow_id = response_json['id']
        print(workflow_id)
    else:
        msg = 'Unexpected response code {0} when sending notification {1} to url {2}: \n{3}'
        raise ValueError(msg.format(response.status_code, args.notification, args.lira_url, response.text))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--lira_url')
    parser.add_argument('--secrets_file')
    parser.add_argument('--notification')
    args = parser.parse_args()
    run(args)
