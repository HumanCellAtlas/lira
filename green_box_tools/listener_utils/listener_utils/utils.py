import requests
import json
import logging
from requests.auth import HTTPBasicAuth
from flask import make_response
from google.cloud import storage
from google.oauth2 import service_account


def get_filename_from_gs_link(link):
    """Get the filename corresponding to a google_storage link.

    :param str link: A string of google cloud storage link.
    :return str: A string of filename.
    """
    return link.split('/')[-1]


def parse_bucket_blob_from_gs_link(path):
    """Utility to split a google storage path into bucket + blob name.

    :param str path: A string of google cloud storage path (must have gs:// prefix)
    :return str: A string of bucket name.
    :return str: A string of blob name
    """
    if not path.startswith('gs://'):
        raise ValueError('%s path is not a valid link')
    (prefix, _, bucket), blob = path.split('/')[:3], path.split('/')[3:]

    return bucket, '/'.join(blob)


def response_with_server_header(body, status=200):
    """Add information of server to header.We are doing this to overwrite the default flask Server header. The
     default header is a security risk because it provides too much information about server internals.

    :param body: HTTP response body content.
    :param int status: HTTP response status code.
    :return: HTTP response with information of server in header.
    """
    response = make_response(json.dumps(body), status)
    response.headers['Server'] = 'Secondary Analysis Service'
    response.headers['Content-type'] = 'application/json'
    return response


def is_authenticated(args, token):
    """Check if is authenticated.

    :param dict args: A dictionary of arguments.
    :param token: Token object.
    :return boolean: True if authenticated else return False.
    """
    return args.get('auth') == token


def extract_uuid_version_subscription_id(msg):
    """Extract uuid, version, subscription_id from message.

    :param dict msg: A dictionary of message contains bundle information.
    :return str uuid: uuid of the bundle.
    :return str version: version of the bundle.
    :return subscription_id: subscription id of the bundle.
    """
    uuid = msg["match"]["bundle_uuid"]
    version = msg["match"]["bundle_version"]
    subscription_id = msg["subscription_id"]
    return uuid, version, subscription_id


def compose_inputs(workflow_name, uuid, version):
    """Create Cromwell inputs file containing bundle uuid and version.

    :param str workflow_name: The name of the workflow.
    :param str uuid: uuid of the bundle.
    :param str version: version of the bundle.
    :return dict: A dictionary of workflow inputs.
    """
    return {workflow_name + '.bundle_uuid': uuid,
            workflow_name + '.bundle_version': str(version)}


def start_workflow(wdl_file, zip_file, inputs_file, inputs_file2, options_file, green_config):
    """Use HTTP POST to start workflow in Cromwell.

    :param str wdl_file: The path to wdl file.
    :param str zip_file: The path to zip file.
    :param str inputs_file: The path to inputs file.
    :param str inputs_file2: The path to inputs file 2.
    :param str options_file: The path to configs file.
    :param config.ListenerConfig green_config: The ListenerConfig class of current app.
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


def download_gcs_blob(authenticated_gcs_client, bucket_name, source_blob_name, destination_file_name=None):
    """Use google.cloud.storage API to download a blob from the bucket.

    :param obj authenticated_gcs_client: An authenticated google cloud storage client object.
    :param str bucket_name: A string of bucket name.
    :param str source_blob_name: A string of source blob name that to be downloaded.
    :param str destination_file_name: A string of destination file name.
    """
    logging.getLogger()

    if not destination_file_name:  # destination_file_name is set to source_blob_name by default
        destination_file_name = './' + source_blob_name

    storage_client = authenticated_gcs_client  # pass the client as a parameter here
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)

    try:
        blob.download_to_filename(destination_file_name)
        logging.info('Blob {0} downloaded to {1}.'.format(source_blob_name, destination_file_name))
    except:
        logging.debug(
            'An error occurred during downloading blob {} from Google Cloud Storage'.format(source_blob_name))


class LazyProperty:
    """This class implements a decorator for lazy-initializing class properties.

        Instead of implementing Singleton Pattern, this decorator accepts multiple
        instances of a class, meanwhile, implements lazy initialization of certain
        decorated property. That specific read-only property only gets initialized
        on access, but once accessed, it would be cached and not re-initialized on
        each access.
    """
    def __init__(self, func):
        self.func = func

    def __get__(self, instance, cls):
        if instance is None:
            return self
        else:
            val = self.func(instance)
            setattr(instance, self.func.__name__, val)


class GoogleCloudStorageClient:
    def __init__(self, key_location, scopes):
        """This class implements the client to interact with Google Cloud Storage.

        :param str key_location: The location of Google Cloud Storage API key.
        :param list scopes: A list of OAuth 2.0 scopes information.
        """
        self.key_location, self.scopes = key_location, scopes

    @LazyProperty
    def storage_client(self):
        logging.getLogger()
        logging.debug('Configuring listener credentials using %s' % self.key_location)
        credentials = service_account.Credentials.from_service_account_file(
            self.key_location, scopes=self.scopes)
        client = storage.Client(credentials=credentials, project=credentials.project_id)
        return client
