#!/usr/bin/env python

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
from google.auth.exceptions import DefaultCredentialsError

# IMPORTANT: setting global client
try:
    key_location = '/etc/secondary-analysis/bucket-reader-key.json'
    client = storage.Client.from_service_account_json(
        key_location)
    print('Configuring listener credentials using %s' % key_location)
except IOError:
    client = storage.Client()
    print('Configuring listener using default credentials')
except DefaultCredentialsError:
    print('Could not configure listener using expected json key or default credentials')
    raise


def verify_gs_link(link):
    """verifies that a google storage endpoint exists and references a file.

    :param str link: link to parse
    :global google.cloud.storage.Client client: authenticated google-cloud-storage client
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




def verify_config_json(config_json):
    """parse the config json file and verify that it contains valid configurations

    :param dict config_json:
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
    for wdl in config_json['wdls']:
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
    if any(a == b for a, b in combinations(config_json, 2)):
        warnings.warn('duplicate wdl definitions detected in config.json')

    # check for duplicate subscription ids
    subscription_ids = [wdl['subscription_id'] for wdl in config_json['wdls']]
    if len(config_json['wdls']) != len(set(subscription_ids)):
        raise ValueError(
            'One or more wdl specifications contains a duplicated subscription ID but '
            'have non-identical configurations. Please check configuration file '
            'contents.')

    # check that link fields point to valid gs endpoints
    for wdl in config_json['wdls']:
        for field, value in wdl.iteritems():
            if field.endswith('link'):
                verify_gs_link(value)


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
