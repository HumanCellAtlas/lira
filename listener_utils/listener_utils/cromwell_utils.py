"""This module contains utility functions to interact with Cromwell.
"""
import requests
from requests.auth import HTTPBasicAuth


def start_workflow(wdl_file, zip_file, inputs_file, inputs_file2, options_file, green_config):
    """Use HTTP POST to start workflow in Cromwell.

    :param _io.BytesIO or file-like object wdl_file: Bytes or file-like object of wdl file.
    :param _io.BytesIO or file-like object zip_file: Bytes or file-like object of zip file.
    :param _io.BytesIO or file-like object inputs_file: Bytes or file-like object of inputs file.
    :param _io.BytesIO or file-like object inputs_file2: Bytes or file-like object of inputs file 2.
    :param _io.BytesIO or file-like object options_file: Bytes or file-like object of configs file.
    :param ListenerConfig green_config: The ListenerConfig class of current app.
    :return requests.Response response: HTTP response from cromwell.
    """
    files = {
        'wdlSource': wdl_file,
        'workflowInputs': inputs_file,
        'workflowInputs_2': inputs_file2,
        'wdlDependencies': zip_file,
        'workflowOptions': options_file
    }

    response = requests.post(
        green_config.cromwell_url, files=files,
        auth=HTTPBasicAuth(green_config.cromwell_user,
                           green_config.cromwell_password))
    return response
