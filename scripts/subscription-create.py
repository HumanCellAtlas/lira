#!/usr/bin/env python

import json
import argparse
from httplib2 import Http
from oauth2client.service_account import ServiceAccountCredentials


def prep_json(callback_base_url, query_json_file, query_param_token, hmac_key_id, hmac_key, attachments_file):
    with open(query_json_file) as f:
        query = json.load(f)

    if hmac_key_id is not None:
        print('Subscribing with hmac key')
        payload = {
            'es_query': query,
            'callback_url': callback_base_url,
            'hmac_key_id': hmac_key_id,
            'hmac_secret_key': hmac_key
        }
    else:
        print('Subscribing with query param token')
        payload = {
            'es_query': query,
            'callback_url': '{0}?auth={1}'.format(callback_base_url, query_param_token)
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
    parser.add_argument('-dss_url', help='Endpoint for creating new subscriptions in the storage service', required=True)
    parser.add_argument('-callback_base_url', help='Lira endpoint for receiving notifications', required=True)
    parser.add_argument('-key_file', help='JSON file containing storage service credentials', required=True)
    parser.add_argument('-query_json', help='JSON file containing the query to register', required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-hmac_key', help='HMAC key')
    group.add_argument('-query_param_token', help='Query param auth token')
    parser.add_argument('-hmac_key_id', help='Unique identifier for hmac key')
    parser.add_argument("--additional_metadata",
                        required=False,
                        default=None,
                        help='JSON file with additional fields to include in the notification')
    args = parser.parse_args()
    if args.hmac_key and not args.hmac_key_id:
        parser.error('You must specify hmac_key_id when you specify hmac_key')

    js = prep_json(
        args.callback_base_url,
        args.query_json,
        args.query_param_token,
        args.hmac_key_id,
        args.hmac_key,
        args.additional_metadata
    )
    make_request(js, args.dss_url, args.key_file)
