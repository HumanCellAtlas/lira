#!/usr/bin/env python

import json
import argparse
from httplib2 import Http
from oauth2client.service_account import ServiceAccountCredentials


def prep_json(callback_base_url, listener_secret, query_json):
    js = {}
    js["callback_url"] = "{0}?auth={1}".format(callback_base_url, listener_secret)

    query = None
    with open(query_json) as f:
        query = json.load(f)
    js["es_query"] = query

    return js

def make_request(js, dss_url, key_file):
    scopes = ['https://www.googleapis.com/auth/userinfo.email']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(key_file, scopes)
    h = credentials.authorize(Http())
    headers = {'Content-type': 'application/json'}
    response, content = h.request(dss_url, 'PUT', body=json.dumps(js), headers=headers)
    print(content)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("dss_url")
    parser.add_argument("callback_base_url")
    parser.add_argument("listener_secret")
    parser.add_argument("key_file")
    parser.add_argument("query_json")
    args = parser.parse_args()
    js = prep_json(args.callback_base_url, args.listener_secret, args.query_json)
    make_request(js, args.dss_url, args.key_file)
