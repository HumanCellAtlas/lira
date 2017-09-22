#!/usr/bin/env/python

"""
Green box description FIXME: elaborate
"""

import os
import json
import logging
import warnings
from itertools import combinations
import connexion
from connexion.resolver import RestyResolver
from google.cloud import storage
from google.cloud.exceptions import NotFound


def verify_gs_link(link, client):
    """verifies that a google storage endpoint exists and references a file.

    note: assumes that you have run `gcloud auth application-default login`
    """
    # split the link, checking to make sure it contains both a bucket and key
    # python3 syntax
    # try:
    #     _, _, bucket, *pseudo_dirs, pseudo_filename = link.split('/')
    # except ValueError:
    #     raise ValueError(
    #         'Malformed google storage link. Link must specify both a bucket '
    #         'and key: {malformed_link}'.format(malformed_link=link))
    fields = link.split('/')
    if len(fields) < 4:
        raise ValueError(
            'Malformed google storage link. Link must specify both a bucket '
            'and key: {malformed_link}'.format(malformed_link=link))
    bucket, pseudo_dirs, pseudo_filename = fields[2], fields[3:-1], fields[-1]

    # verify the bucket exists
    try:
        verified_bucket = client.get_bucket(bucket)
        assert verified_bucket.exists(), 'Bucket: {bucket} does not exist!'.format(
            bucket=bucket)
    except NotFound:
        raise ValueError(
            'Bucket {bucket} specified in {link} does not exist.'.format(
                bucket=bucket, link=link))

    # verify the file (blob) exists in the bucket
    blob_name = '/'.join(pseudo_dirs + [pseudo_filename])
    if not verified_bucket.blob(blob_name).exists():
        raise ValueError(
            'specified blob (alias: key, filename) does not exist in {bucket}: '
            '{blob_name}'.format(bucket=bucket, blob_name=blob_name))


def verify_config_json(parsed_json_dict):
    """parse the config json file and verify that it contains valid configurations

    :param dict parsed_json_dict:
    :return:
    """

    # check for missing or unexpected config fields
    expected_fields = {
        'subscription_id',
        'wdl_link',
        'workflow_name',
        'wdl_deps_link',
        'default_inputs_link'
    }
    for wdl in parsed_json_dict['wdls']:
        wdl_keys = set(wdl.keys())
        extra_keys = wdl_keys - expected_fields
        missing_keys = expected_fields - wdl_keys
        if missing_keys:
            raise ValueError('\nThe following WDL configuration is missing key(s): '
                             '{keys}\n{wdl}'
                             ''.format(wdl=wdl, keys=', '.join(missing_keys)))
        if extra_keys:
            raise ValueError('\nThe following WDL configuration has unexpected key(s): '
                             '{keys}\n{wdl}'
                             ''.format(wdl=wdl, keys=', '.join(extra_keys)))

    # check for duplicate wdl definitions
    if any(a == b for a, b in combinations(parsed_json_dict, 2)):
        warnings.warn('duplicate wdl definitions detected in config.json')

    # check for duplicate subscription ids
    subscription_ids = [wdl['subscription_id'] for wdl in parsed_json_dict['wdls']]
    if len(parsed_json_dict['wdls']) != len(set(subscription_ids)):
        raise ValueError(
            'One or more wdl specifications contains a duplicated subscription ID but '
            'have identical configuration. Please check configuration file contents.')

    # check that link fields point to valid gs endpoints
    client = storage.Client()  # this is slow, do this only once
    for wdl in parsed_json_dict['wdls']:
        for field, value in wdl.iteritems():
            if field.endswith('link'):
                verify_gs_link(value, client)


def main():
    logging.basicConfig(level=logging.DEBUG)

    app = connexion.App(__name__)
    app.app.config['MAX_CONTENT_LENGTH'] = 10 * 1000

    config_path = os.environ['listener_config']
    with open(config_path) as f:
        config = json.load(f)
        verify_config_json(config)
        for key in config:
            app.app.config[key] = config[key]

    resolver = RestyResolver("green_box.api", collection_endpoint_name="list")
    app.add_api('../green_box.yml', resolver=resolver, validate_responses=True)
    return app

if __name__ == "__main__":
    app = main()
    app.run(debug=True, port=8080)
