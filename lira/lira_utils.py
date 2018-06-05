"""This module contains utility functions and classes of listener.
"""
import json
import logging
from cromwell_tools import cromwell_tools
from flask import make_response
from urllib.parse import urlparse
from collections import namedtuple
from requests_http_signature import HTTPSignatureAuth
import hashlib
import base64
import email.utils
from datetime import datetime, timedelta, timezone


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


def is_authenticated(request, config):
    """Check if message is authentic.

    Args:
        request: The request object
        config (LiraConfig): Lira's configuration

    Returns:
        True if message verifiably came from storage service, else False.
    """
    if hasattr(config, 'hmac_key'):
        return _is_authenticated_hmac(request, config.hmac_key, config.stale_notification_timeout)
    else:
        return _is_authenticated_query_param(request.args, config.notification_token)


def _is_authenticated_hmac(request, hmac_key, stale_notification_timeout=0):
    """Check if message is authentic

    Args:
        request: the request object
        hmac_key (bytes): the hmac key
        stale_notification_timeout (int): timeout beyond which we refuse to accept the message,
    even if everything else checks out

    Returns:
        True if message is verifiably from the storage service, False otherwise
    """
    # Since we use the same key and algorithm for all subscriptions,
    # we will always try to verify notifications with that one.
    def key_resolver(key_id, algorithm):
        return hmac_key

    try:
        # Make sure there's an auth header with a valid signature
        auth_header = request.headers.get('Authorization')
        if auth_header and 'date' not in auth_header:
            raise AssertionError('No date in auth header: {0}'.format(auth_header))
        HTTPSignatureAuth.verify(request, key_resolver=key_resolver)

        # Make sure notification isn't too old
        _check_date(request.headers.get('Date'), stale_notification_timeout)

        # Make sure given body digest and calculated digest match
        digest_from_header = request.headers.get('Digest')
        calculated_digest = _calculate_digest(request)
        if calculated_digest != digest_from_header:
            logger.error('Auth error: digests do not match')
            return False
        return True
    except AssertionError as e:
        logger.error('Auth error: {0}'.format(e))
        return False


def _check_date(date_header, stale_notification_timeout):
    """Verify that there is a date header and the message isn't too old.

    Args:
        date_header (str): timestamp indicating date/time message was sent
        stale_notification_timeout (int): message age in seconds beyond which we refuse to accept it

    Raises:
        AssertionError if there is no date header or the message is too old
    """
    if not date_header:
        raise AssertionError('No date header')
    datetime_from_header = email.utils.parsedate_to_datetime(date_header)
    diff = datetime.now(timezone.utc) - datetime_from_header
    if diff > timedelta(seconds=stale_notification_timeout) and stale_notification_timeout > 0:
        raise AssertionError('Message is more than {0} seconds old'.format(stale_notification_timeout))


def _calculate_digest(request):
    """Calculate the digest of the request body and make a string of the type
    expected by the requests-http-signature library.

    Args:
        request: the request object

    Returns:
        (str) containing digest
    """
    raw_digest = hashlib.sha256(request.get_data()).digest()
    digest_string = "SHA-256=" + base64.b64encode(raw_digest).decode()
    return digest_string


def _is_authenticated_query_param(params, token):
    return params.get('auth') == token


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


def compose_inputs(workflow_name, uuid, version, lira_config):
    """Create Cromwell inputs file containing bundle uuid and version.

    Args:
        workflow_name (str): The name of the workflow.
        uuid (str): uuid of the bundle.
        version (str): version of the bundle.
        lira_config (LiraConfig): Lira configuration

    Returns:
        A dictionary of workflow inputs.
    """
    return {
        workflow_name + '.bundle_uuid': uuid,
        workflow_name + '.bundle_version': version,
        workflow_name + '.runtime_environment': lira_config.env,
        workflow_name + '.dss_url': lira_config.dss_url,
        workflow_name + '.submit_url': lira_config.ingest_url,
        workflow_name + '.use_caas': lira_config.use_caas
    }


def compose_caas_options(cromwell_options_file, lira_config):
    """ Append options for using Cromwell-as-a-service to the default options.json file in the wdl config.

    Args:
        cromwell_options_file (str): Contents of the options.json file in the wdl config
        lira_config (LiraConfig): Lira configuration

    Returns:
        A dictionary of workflow outputs.
    """
    options_file = cromwell_options_file
    if isinstance(options_file, bytes):
        options_file = cromwell_options_file.decode()
    options_json = json.loads(options_file)

    with open(lira_config.caas_key) as f:
        caas_key = f.read()
    options_json.update({
        'jes_gcs_root': lira_config.gcs_root,
        'google_project': lira_config.google_project,
        'user_service_account_json': caas_key
    })
    return options_json


def parse_github_resource_url(url):
    """Parse a URL which describes a resource file on Github.

    A valid URL here means either a valid url to a file on Github, either in raw format or not. For example,
     both https://github.com/HumanCellAtlas/lira/blob/master/README.md and
     https://raw.githubusercontent.com/HumanCellAtlas/lira/master/README.md are valid github resource URL here.

    :param str url: A valid URL which describes a resource file on Github.

    :return collections.namedtuple: A namedtuple with information about: URI scheme, netloc,
     owner(either User or Organization), repo, version(either git tags or branch name), path, file.

    :raises ValueError: Raise a ValueError when the input URL is invalid.
    """
    if url.startswith('git@') or url.endswith('.git'):
        raise ValueError('{} is not a valid url to a resource file on Github.'.format(url))

    ParseResult = namedtuple('ParseResult', 'scheme netloc owner repo version path file')

    intermediate_result = urlparse(url)
    scheme, netloc, path_array = intermediate_result.scheme, intermediate_result.netloc,\
                                 intermediate_result.path.split('/')

    if netloc == 'github.com':
        owner, repo, version, file = path_array[1], path_array[2], path_array[4], path_array[-1]
        path = '/'.join(path_array[5:])
    elif netloc == 'raw.githubusercontent.com':
        owner, repo, version, file = path_array[1], path_array[2], path_array[3], path_array[-1]
        path = '/'.join(path_array[4:])
    else:
        owner = repo = version = path = file = None
    return ParseResult(scheme=scheme, netloc=netloc, owner=owner, repo=repo, version=version, path=path, file=file)


def legalize_cromwell_labels(label):
    """Legalize invalid labels so that they can be accepted by Cromwell.

    Note: This is a very temporary solution, once Cromwell is more permissive on labels, this function should be
     deprecated right away. This function will convert integers to strings, all Upper letters to lower letters,
     replace all '_' to '-', replace all '.' to '-', and replace all ':' to '-'.

    :param str label: A string of key/value of labels need to be legalized.

    :return str: A converted, uglified but legal version of label.
    """
    return label.lower().replace('_', '-').replace('.', '-').replace(':', '-')


def compose_labels(workflow_name, workflow_version, bundle_uuid, bundle_version, extra_labels=None):
    """Create Cromwell labels object containing pre-defined labels and possible extra labels.

    The pre-defined workflow labels are: workflow_name, workflow_version, bundle_uuid, bundle_version.
     This function also accepts dictionary as extra labels.

    :param str workflow_name: The name of the workflow.
    :param str workflow_version: Version of the workflow.
    :param str bundle_uuid: Uuid of the bundle.
    :param str bundle_version: Version of the bundle.
    :param dict extra_labels: A dictionary of extra labels.

    :return dict: A dictionary of composed workflow labels.
    """
    workflow_labels = {
        "workflow-name": legalize_cromwell_labels(workflow_name),
        "workflow-version": legalize_cromwell_labels(workflow_version),
        "bundle-uuid": legalize_cromwell_labels(bundle_uuid),
        "bundle-version": legalize_cromwell_labels(bundle_version)
    }
    if isinstance(extra_labels, dict):
        extra_labels = {legalize_cromwell_labels(k): legalize_cromwell_labels(v) for k, v in extra_labels.items()}
        workflow_labels.update(extra_labels)

    return workflow_labels


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
