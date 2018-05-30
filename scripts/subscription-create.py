#!/usr/bin/env python

import json
import argparse
from httplib2 import Http
from oauth2client.service_account import ServiceAccountCredentials


def prep_json(callback_base_url, listener_secret, query_json_file, attachments_file=None):
    with open(query_json_file) as f:
        query = json.load(f)

    payload = {
        'es_query': query,
        'callback_url': '{0}?auth={1}'.format(callback_base_url, listener_secret)
    }

    if attachments_file:
        with open(attachments_file) as f:
            attachments = json.load(f)
        payload['attachments'] = attachments

    return payload


def make_request(js, dss_url, key_file):
    scopes = ['https://www.googleapis.com/auth/userinfo.email']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(key_file, scopes)
    h = credentials.authorize(Http())
    headers = {'Content-type': 'application/json'}
    response, content = h.request(dss_url, 'PUT', body=json.dumps(js), headers=headers)
    print(content)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("dss_url", help='Endpoint for creating new subscriptions in the storage service')
    parser.add_argument("callback_base_url", help='Listener endpoint for receiving notifications')
    parser.add_argument("listener_secret", help='Auth key for listener')
    parser.add_argument("key_file", help='JSON file containing storage service credentials')
    parser.add_argument("query_json", help='JSON file containing the query to register')
    parser.add_argument("--additional_metadata",
                        required=False,
                        help='JSON file with additional fields to include in the notification')
    args = parser.parse_args()
    js = prep_json(args.callback_base_url, args.listener_secret, args.query_json, args.additional_metadata)
    make_request(js, args.dss_url, args.key_file)
