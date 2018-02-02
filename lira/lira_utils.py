"""This module contains utility functions and classes of listener.
"""
import json
import logging
from flask import make_response


def response_with_server_header(body, status):
    """Add information of server to header.We are doing this to overwrite the default flask Server header. The
     default header is a security risk because it provides too much information about server internals.

    :param obj body: HTTP response body content that is JSON-serializable.
    :param int status: HTTP response status code.
    :return flask.wrappers.Response response: HTTP response with information of server in header.
    """
    response = make_response(json.dumps(body, indent=2) + '\n', status)
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


def noop_lru_cache(maxsize=None, typed=False):
    """Decorator that serves as a mock of the functools.lru_cache decorator, which
    is only available in Python 3. We use this mock as a placeholder in Python 2
    to avoid blowing up when the real decorator isn't available. It merely
    calls through to the decorated function and provides a dummy cache_info()
    function.
    """
    def cache_info():
        return 'No cache info available. Cache is disabled.'

    def cache_clear():
        pass

    def real_noop_lru_cache(fn):
        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)
        wrapper.cache_info = cache_info
        wrapper.cache_clear = cache_clear
        return wrapper
    return real_noop_lru_cache
