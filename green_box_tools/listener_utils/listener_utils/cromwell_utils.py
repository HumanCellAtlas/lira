"""This module contains utility functions to interact with Cromwell.
"""
import requests
from requests.auth import HTTPBasicAuth


def start_workflow(wdl_file, zip_file, inputs_file, inputs_file2, options_file, green_config):
    """Use HTTP POST to start workflow in Cromwell.

    :param str wdl_file: The path to wdl file.
    :param str zip_file: The path to zip file.
    :param str inputs_file: The path to inputs file.
    :param str inputs_file2: The path to inputs file 2.
    :param str options_file: The path to configs file.
    :param ListenerConfig green_config: The ListenerConfig class of current app.
    :return requests.Response response: HTTP response from cromwell.
    """
    with open(wdl_file, 'rb') as wdl, open(zip_file, 'rb') as deps, \
            open(inputs_file, 'rb') as inputs, open(inputs_file2, 'rb') as inputs2, \
            open(options_file, 'rb') as options:
        files = {
            'wdlSource': wdl,
            'workflowInputs': inputs,
            'workflowInputs_2': inputs2,
            'wdlDependencies': deps,
            'workflowOptions': options
        }

        response = requests.post(
            green_config.cromwell_url, files=files,
            auth=HTTPBasicAuth(green_config.cromwell_user,
                               green_config.cromwell_password))
        return response
