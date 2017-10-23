"""This module contains utility functions and classes to interact with Google Cloud Storage Service.
"""
import logging
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


def download_gcs_blob(authenticated_gcs_client, bucket_name, source_blob_name, destination_file_name=None):
    """Use google.cloud.storage API to download a blob from the bucket.

    :param google.cloud.storage.client.Client authenticated_gcs_client: An authenticated google cloud storage client.
    :param str bucket_name: A string of bucket name.
    :param str source_blob_name: A string of source blob name that to be downloaded.
    :param str destination_file_name: A string of destination file name.
    """
    logging.getLogger()

    if not destination_file_name:  # destination_file_name is set to source_blob_name by default
        destination_file_name = './' + source_blob_name

    bucket = authenticated_gcs_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(destination_file_name)


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
