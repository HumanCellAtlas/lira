"""This module contains utility functions and classes of listener.
"""
import json
import logging
from cromwell_tools import cromwell_tools
from flask import make_response

logger = logging.getLogger('lira.{module_path}'.format(module_path=__name__))


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


def create_prepare_submission_function(cache_wdls):
    """Returns decorated prepare_submission function. Decorator is determined as follows:
    Python 2: Always decorate with noop_lru_cache, since functools.lru_cache is not available in 2.
    Python 3: Use functools.lru_cache if cache_wdls is true, otherwise use noop_lru_cache."""

    # Use noop_lru_cache unless cache_wdls is true and functools.lru_cache is available
    lru_cache = noop_lru_cache
    if not cache_wdls:
        logger.info('Not caching wdls because Lira is configured with cache_wdls false')
    else:
        try:
            from functools import lru_cache
        except ImportError:
            logger.info('Not caching wdls because functools.lru_cache is not available in Python 2.')

    @lru_cache(maxsize=None)
    # Setting maxsize to None here means each unique call to prepare_submission (defined by parameters used)
    # will be added to the cache without evicting any other items. Additional non-unique calls
    # (parameters identical to a previous call) will read from the cache instead of actually
    # calling this function. This means that the function will be called no more than once for
    # each wdl config, but we can have arbitrarily many wdl configs without running out of space
    # in the cache.
    def prepare_submission(wdl_config, submit_wdl):
        """Load into memory all static data needed for submitting a workflow to Cromwell"""

        # Read files into memory
        wdl_file = cromwell_tools.download(wdl_config.wdl_link)
        wdl_static_inputs_file = cromwell_tools.download(wdl_config.wdl_static_inputs_link)
        options_file = cromwell_tools.download(wdl_config.options_link)

        # Create zip of analysis and submit wdls
        url_to_contents = cromwell_tools.download_to_map(wdl_config.analysis_wdls + [submit_wdl])
        wdl_deps_dict = url_to_contents

        return CromwellSubmission(wdl_file, wdl_static_inputs_file, options_file, wdl_deps_dict)

    return prepare_submission


class CromwellSubmission(object):
    """Holds static data needed for submitting a workflow to Cromwell, including
    the top level wdl file, the static inputs json file, the options file,
    and the dependencies zip file.
    """

    def __init__(self, wdl_file, wdl_static_inputs_file=None, options_file=None, wdl_deps_dict=None):
        self.wdl_file = wdl_file
        self.wdl_static_inputs_file = wdl_static_inputs_file
        self.options_file = options_file
        self.wdl_deps_dict = wdl_deps_dict
