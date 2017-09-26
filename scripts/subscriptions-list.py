#!/usr/bin/env python

import json
import argparse
from httplib2 import Http
from oauth2client.service_account import ServiceAccountCredentials


def run(dss_url, key_file):
    scopes = ['https://www.googleapis.com/auth/userinfo.email']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(key_file, scopes)
    h = credentials.authorize(Http())
    response, content = h.request(dss_url, 'GET')
    print(content)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('dss_url')
    parser.add_argument('key_file')
    args = parser.parse_args()
    run(args.dss_url, args.key_file)
