#!/usr/bin/env python

"""
Green box description FIXME: elaborate
"""

import os
import json
import logging
import connexion
import warnings
from connexion.resolver import RestyResolver


# todo implement using google.cloud.storage api; requires OAuth, secrets
# todo alternative: reference only public files; would rather not assume gcloud cmdline access
def verify_gs_link():
    raise NotImplementedError


def verify_config_json(parsed_json_dict):
    """parse the config json file and verify that it contains valid configurations

    :param dict parsed_json_dict:
    :return:
    """
    # check for duplicate objects with the same subscription id
    if len(parsed_json_dict['wdls']) != len(set(parsed_json_dict['wdls'])):
        warnings.warn('duplicate wdl definitions detected in config.json')

    # check for duplicate subscription ids
    subscription_ids = [wdl['subscription_id'] for wdl in parsed_json_dict['wdls']]
    if len(parsed_json_dict['wdls']) != len(set(subscription_ids)):
        raise ValueError('One or more wdl specifications contains a duplicated subscription ID but '
                         'have identical configuration. Please check configuration file contents.')

    # todo check for any object that has an invalid gs path.

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
        missing_keys = wdl_keys - expected_fields
        extra_keys = expected_fields - wdl_keys
        if missing_keys:
            raise ValueError('{wdl} has missing key(s): {keys}'.format(
                wdl=wdl, keys=', '.join(wdl_keys)))
        if extra_keys:
            raise ValueError('{wdl} has unexpected keys(s): {keys}'.format(
                wdl=wdl, keys=', '.join(wdl_keys)))


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
