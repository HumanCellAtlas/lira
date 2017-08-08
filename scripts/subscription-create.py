#!/usr/bin/env python

import json
import requests
import argparse

def run(dss_url, callback_base_url, oauth_token, listener_secret):
    js = {}
    js["callback_url"] = "{0}?auth={1}".format(callback_base_url, listener_secret)

    query = None
    with open("smartseq2-query.json") as f:
        query = json.load(f)
    js["query"] = query

    headers = {"Authorization": "Bearer {0}".format(oauth_token), "Content-type": "application/json"}
    response = requests.put(dss_url, headers=headers, data=json.dumps(js))
    print(response)
    print(response.text)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("dss_url")
    parser.add_argument("callback_base_url")
    parser.add_argument("oauth_token")
    parser.add_argument("listener_secret")
    args = parser.parse_args()
    run(args.dss_url, args.callback_base_url, args.oauth_token, args.listener_secret)
