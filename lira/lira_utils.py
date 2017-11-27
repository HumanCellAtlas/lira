"""This module contains utility functions and classes of listener.
"""
import json
import logging
from flask import make_response
import io
import requests
import zipfile
from StringIO import StringIO


def response_with_server_header(body, status=200):
    """Add information of server to header.We are doing this to overwrite the default flask Server header. The
     default header is a security risk because it provides too much information about server internals.

    :param obj body: HTTP response body content that is JSON-serializable.
    :param int status: HTTP response status code.
    :return flask.wrappers.Response response: HTTP response with information of server in header.
    """
    response = make_response(json.dumps(body), status)
    response.headers['Server'] = 'Secondary Analysis Service'
    response.headers['Content-type'] = 'application/json'
    return response


def is_authenticated(args, token):
    """Check if is authenticated.

    :param dict args: A dictionary of arguments.
    :param str token: Notification token string in listener's notification config file.
    :return boolean: True if authenticated else return False.
    """
    return args.get('auth') == token


def extract_uuid_version_subscription_id(msg):
    """Extract uuid, version, subscription_id from message.

    :param dict msg: A dictionary of message contains bundle information.
    :return str uuid: uuid of the bundle.
    :return str version: version of the bundle.
    :return str subscription_id: subscription id of the bundle.
    """
    uuid = msg["match"]["bundle_uuid"]
    version = msg["match"]["bundle_version"]
    subscription_id = msg["subscription_id"]
    return uuid, version, subscription_id


def compose_inputs(workflow_name, uuid, version, env):
    """Create Cromwell inputs file containing bundle uuid and version.

    :param str workflow_name: The name of the workflow.
    :param str uuid: uuid of the bundle.
    :param str version: version of the bundle.
    :param str env: runtime environment, such as 'dev', 'staging', 'int' or 'prod'.
    :return dict: A dictionary of workflow inputs.
    """
    return {
        workflow_name + '.bundle_uuid': uuid,
        workflow_name + '.bundle_version': version,
        workflow_name + '.runtime_environment': env
    }


def download_to_map(urls):
    """
    Reads contents from each url into memory and returns a
    map of urls to their contents
    """
    url_to_contents = {}
    for url in urls:
        contents = download(url)
        url_to_contents[url] = contents
    return url_to_contents


def make_zip_in_memory(url_to_contents):
    """
    Given a map of urls and their contents, returns an in-memory zip file
    containing each file. For each url, the part after the last slash is used
    as the file name when writing to the zip archive.
    """
    buf = StringIO()
    with zipfile.ZipFile(buf, 'w') as zip_buffer:
        for url, contents in url_to_contents.items():
            name = url.split('/')[-1]
            zip_buffer.writestr(name, contents)

    bytes_buf = io.BytesIO(buf.getvalue())
    return bytes_buf


def download(url):
    """
    Reads the contents located at the url into memory and returns them.
    Urls starting with http are fetched with an http request. All others are
    assumed to be local file paths and read from the local file system.
    """
    if url.startswith('http'):
        return download_http(url)
    else:
        return read_local_file(url)


def download_http(url):
    """
    Makes an http request for the contents at the given url and returns the response body.
    """
    response = requests.get(url)
    response_str = response.text.encode('utf-8')
    return response_str


def read_local_file(path):
    """
    Reads the file contents and returns them.
    """
    with open(path) as f:
        contents = f.read()
    return contents
