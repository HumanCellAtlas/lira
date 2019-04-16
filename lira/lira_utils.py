"""This module contains utility functions and classes of lira.
"""
import json
import logging
from flask import make_response
from urllib.parse import urlparse
from collections import namedtuple
from requests_http_signature import HTTPSignatureAuth
import hashlib
import base64
import email.utils
from datetime import datetime, timedelta, timezone
import cromwell_tools


logger = logging.getLogger(f'lira.{__name__}')


LIRA_SERVER_HEADER = {'Server': 'Lira Service', 'Content-type': 'application/json'}


def response_with_server_header(body, status):
    """Add information of server to header.

    We are doing this to overwrite the default flask Server header. The default header is a security risk because
    it provides too much information about server internals, such as the versions of Python and Werkzeug.

    Args:
        body (obj): HTTP response body content that is JSON-serializable.
        status (status): HTTP response status code.

    Returns:
        response (flask.wrappers.Response response): HTTP response with information of server in header.
    """
    response = make_response(json.dumps(body, indent=2) + '\n', status)
    response.headers.update(LIRA_SERVER_HEADER)
    return response


def is_authenticated(request, config):
    """Check if message is authentic.

    Args:
        request: The request object.
        config (LiraConfig): Lira's configuration.

    Returns:
        True if message verifiably came from storage service, else False.
    """
    if hasattr(config, 'hmac_key'):
        return _is_authenticated_hmac(
            request, config.hmac_key, config.stale_notification_timeout
        )
    else:
        return _is_authenticated_query_param(request.args, config.notification_token)


def _is_authenticated_hmac(request, hmac_key, stale_notification_timeout=0):
    """Check if message is authentic.

    Args:
        request: The request object.
        hmac_key (bytes): The hmac key.
        stale_notification_timeout (int): Timeout beyond which we refuse to accept the message,
            even if everything else checks out.

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
            raise AssertionError(f"No date in auth header: {auth_header}")
        HTTPSignatureAuth.verify(request, key_resolver=key_resolver)

        # Make sure notification isn't too old
        _check_date(request.headers.get('Date'), stale_notification_timeout)

        # Make sure given body digest and calculated digest match
        digest_from_header = request.headers.get('Digest')
        calculated_digest = _calculate_digest(request)
        if calculated_digest != digest_from_header:
            logger.error("Auth error: digests do not match")
            return False
        return True
    except AssertionError as e:
        logger.error(f"Auth error: {e}")
        return False


def _check_date(date_header, stale_notification_timeout):
    """Verify that there is a date header and the message isn't too old.

    Args:
        date_header (str): Timestamp indicating date/time message was sent.
        stale_notification_timeout (int): Message age in seconds beyond which we refuse to accept it.

    Raises:
        AssertionError: If there is no date header or the message is too old.
    """
    if not date_header:
        raise AssertionError("No date header")
    datetime_from_header = email.utils.parsedate_to_datetime(date_header)
    diff = datetime.now(timezone.utc) - datetime_from_header
    if (
        diff > timedelta(seconds=stale_notification_timeout)
        and stale_notification_timeout > 0
    ):
        raise AssertionError(
            f"Message is more than {stale_notification_timeout} seconds old"
        )


def _calculate_digest(request):
    """Calculate the digest of the request body and make a string of the type expected by the
    requests-http-signature library.

    Args:
        request: The request object.

    Returns:
        digest_string (str): A string of digest.
    """
    raw_digest = hashlib.sha256(request.get_data()).digest()
    digest_string = 'SHA-256=' + base64.b64encode(raw_digest).decode()
    return digest_string


def _is_authenticated_query_param(params, token):
    """Check if message is authentic.

    Args:
        params (dict): A dict of the HTTP request parameters.
        token (str): The predefined security token.

    Returns:
        bool: True if the auth param matches the token, False if not.
    """
    return params.get('auth') == token


def extract_uuid_version_subscription_id(msg):
    """Extract uuid, version, subscription_id from message.

    Args:
        msg (dict): A dictionary of message contains bundle information.

    Returns:
        tuple: A tuple of (uuid, version, subscription_id). uuid is a string of the UUID of the bundle. version is a
            string of the version of the bundle. subscription_id is a string of the subscription id.
    """
    uuid = msg['match']['bundle_uuid']
    version = msg['match']['bundle_version']
    subscription_id = msg['subscription_id']
    return uuid, version, subscription_id


def compose_inputs(workflow_name, uuid, version, lira_config):
    """Create Cromwell inputs file containing bundle uuid and version.

    Args:
        workflow_name (str): The name of the workflow.
        uuid (str): uuid of the bundle.
        version (str): version of the bundle.
        lira_config (LiraConfig): Lira configuration

    Returns:
        dict: A dictionary of workflow inputs.
    """
    return {
        workflow_name + '.bundle_uuid': uuid,
        workflow_name + '.bundle_version': version,
        workflow_name + '.runtime_environment': lira_config.env,
        workflow_name + '.dss_url': lira_config.dss_url,
        workflow_name + '.submit_url': lira_config.ingest_url,
        workflow_name + '.schema_url': lira_config.schema_url,
        workflow_name + '.max_cromwell_retries': lira_config.max_cromwell_retries,
        workflow_name + '.cromwell_url': lira_config.cromwell_url,
    }


def compose_caas_options(cromwell_options_file, lira_config):
    """ Append options for using Cromwell-as-a-service to the default options.json file in the wdl config.

    Note: These options only work with Cromwell instances that use the Google Cloud Backend and allow
    user-service-account authentication, such as Cromwell.

    Args:
        cromwell_options_file (str): Contents of the options.json file in the wdl config.
        lira_config (LiraConfig): Lira configuration.

    Returns:
        dict: A dictionary of workflow outputs.
    """
    options_file = cromwell_options_file
    if isinstance(options_file, bytes):
        options_file = cromwell_options_file.decode()
    options_json = json.loads(options_file)

    with open(lira_config.caas_key) as f:
        caas_key = f.read()
        caas_key_json = json.loads(caas_key)

    options_json.update(
        {
            'jes_gcs_root': lira_config.gcs_root,
            'google_project': lira_config.google_project,
            'user_service_account_json': caas_key,
            'google_compute_service_account': caas_key_json['client_email'],
        }
    )
    return options_json


def parse_github_resource_url(url):
    """Parse a URL which describes a resource file on Github.

    A valid URL here means either a valid url to a file on Github, either in raw format or not. For example,
    both https://github.com/HumanCellAtlas/lira/blob/master/README.md and
    https://raw.githubusercontent.com/HumanCellAtlas/lira/master/README.md are valid github resource URL here.

    Args:
        url (str): A valid URL which describes a resource file on Github.

    Returns:
        collections.namedtuple: A namedtuple with information about: URI scheme, netloc,
            owner(either User or Organization), repo, version(either git tags or branch name), path, file.

    Raises:
        ValueError: Raise a ValueError if the input URL is invalid.
    """
    if url.startswith('git@') or url.endswith('.git'):
        raise ValueError(f"{url} is not a valid url to a resource file on Github.")

    ParseResult = namedtuple(
        'ParseResult', 'scheme netloc owner repo version path file'
    )

    intermediate_result = urlparse(url)
    scheme, netloc, path_array = (
        intermediate_result.scheme,
        intermediate_result.netloc,
        intermediate_result.path.split('/'),
    )

    if netloc == 'github.com':
        owner, repo, version, file = (
            path_array[1],
            path_array[2],
            path_array[4],
            path_array[-1],
        )
        path = '/'.join(path_array[5:])
    elif netloc == 'raw.githubusercontent.com':
        owner, repo, version, file = (
            path_array[1],
            path_array[2],
            path_array[3],
            path_array[-1],
        )
        path = '/'.join(path_array[4:])
    else:
        owner = repo = version = path = file = None
    return ParseResult(
        scheme=scheme,
        netloc=netloc,
        owner=owner,
        repo=repo,
        version=version,
        path=path,
        file=file,
    )


def legalize_cromwell_labels(label):
    """Legalize invalid labels so that they can be accepted by Cromwell.

    Note: Cromwell v32 and later versions are permissive and accepting all sort of valid JSON strings, but with a
    length limitation of 255. This function will subset the first 255 characters for too long string values.

    Args:
        label (str | list | None): A string or a list of a string of key/value of labels need to be legalized.

    Returns:
        str: A string of label with no more than 255 characters.

    Raises:
        ValueError: This will happen if the value of the label is a list, and the length of it is not equal to 1.

    """
    cromwell_label_maximum_length = 255

    if isinstance(label, list):
        if len(label) != 1:
            raise ValueError(f"{label} should contain exactly one element!")
        label = label[0]
    return str(label)[:cromwell_label_maximum_length]


def compose_labels(
    workflow_name, workflow_version, bundle_uuid, bundle_version, *extra_labels
):
    """Create Cromwell labels object containing pre-defined labels and potential extra labels.

    The pre-defined workflow labels are: workflow_name, workflow_version, bundle_uuid, bundle_version.
    This function also accepts dictionary as extra labels.

    Args:
        workflow_name (str): The name of the workflow.
        workflow_version (str): version of the workflow.
        bundle_uuid (str): uuid of the bundle.
        bundle_version (str): version of the bundle.
        *extra_labels: Variable length extra label list.

    Returns:
        workflow_labels (dict): A dictionary of the composed workflow labels.
    """
    workflow_labels = {
        'workflow-name': legalize_cromwell_labels(workflow_name),
        'workflow-version': legalize_cromwell_labels(workflow_version),
        'bundle-uuid': legalize_cromwell_labels(bundle_uuid),
        'bundle-version': legalize_cromwell_labels(bundle_version),
    }
    for extra_label in extra_labels:
        if isinstance(extra_label, dict):
            extra_label = {
                legalize_cromwell_labels(k): legalize_cromwell_labels(v)
                for k, v in extra_label.items()
            }
            workflow_labels.update(extra_label)
    return workflow_labels


def noop_lru_cache(maxsize=None, typed=False):
    """Decorator that serves as a mock of the functools.lru_cache decorator, which
    is only available in Python 3. We use this mock as a placeholder in Python 2
    to avoid blowing up when the real decorator isn't available. It merely
    calls through to the decorated function and provides a dummy cache_info()
    function.
    """

    def cache_info():
        return "No cache info available. Cache is disabled."

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
    Python 3: Use functools.lru_cache if cache_wdls is true, otherwise use noop_lru_cache.
    """

    # Use noop_lru_cache unless cache_wdls is true and functools.lru_cache is available
    lru_cache = noop_lru_cache
    if not cache_wdls:
        logger.info("Not caching wdls because Lira is configured with cache_wdls false")
    else:
        try:
            from functools import lru_cache
        except ImportError:
            logger.info(
                "Not caching wdls because functools.lru_cache is not available in Python 2."
            )

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
        wdl_file = cromwell_tools.utilities.download(wdl_config.wdl_link)
        wdl_static_inputs_file = cromwell_tools.utilities.download(
            wdl_config.wdl_static_inputs_link
        )
        options_file = cromwell_tools.utilities.download(wdl_config.options_link)

        # Create zip of analysis and submit wdls
        url_to_contents = cromwell_tools.utilities.download_to_map(
            wdl_config.analysis_wdls + [submit_wdl]
        )
        wdl_deps_dict = url_to_contents

        return CromwellSubmission(
            wdl_file, wdl_static_inputs_file, options_file, wdl_deps_dict
        )

    return prepare_submission


class CromwellSubmission(object):
    """Holds static data needed for submitting a workflow to Cromwell, including
    the top level wdl file, the static inputs json file, the options file,
    and the dependencies zip file.
    """

    def __init__(
        self,
        wdl_file,
        wdl_static_inputs_file=None,
        options_file=None,
        wdl_deps_dict=None,
    ):
        self.wdl_file = wdl_file
        self.wdl_static_inputs_file = wdl_static_inputs_file
        self.options_file = options_file
        self.wdl_deps_dict = wdl_deps_dict
