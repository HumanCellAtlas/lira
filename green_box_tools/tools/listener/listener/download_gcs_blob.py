#!/usr/bin/env python3

import logging
from google.cloud import storage
from google.auth.exceptions import DefaultCredentialsError
from google.oauth2 import service_account
from .config import ListenerConfig
logging.basicConfig(level=logging.DEBUG)


class Download_gcs_blob(object):

    def __init__(self,
                 key_location='/etc/secondary-analysis/bucket-reader-key.json',
                 scopes=['https://www.googleapis.com/auth/devstorage.read_only']):
        """Class that handles google cloud storage's authentication and download for the listener.

        This object takes a string of location of secret-key, and a list of OAuth 2.0 scopes
            as parameter. Then handles authentication with google cloud storage and stores 
            the authenticated client as a class variable for downloading blobs from GCS. For 
            a full list of scopes, check the link: 
            https://developers.google.com/identity/protocols/googlescopes

        :param str key_location: location of the secret key to be used for authentication
        :param list scopes: the OAuth 2.0 scopes that need to request to access Google APIs
        """
        try:
            credentials = service_account.Credentials.from_service_account_file(
                key_location, scopes=scopes)
            storage_client = storage.Client(credentials=credentials, project=credentials.project_id)
            logging.debug('Configuring listener credentials using %s' % key_location)

            self.storage_client = storage_client  # Store the authenticated client

        except IOError:
            logging.debug(
                'Could not configure listener using expected json key or default credentials')


    def download_gcs_blob(self, bucket_name, source_blob_name, destination_file_path='./', destination_file_name=None):
    """Use google.cloud.storage API to download a blob from the bucket."""
        if not destination_file_name:  # destination_file_name is set to source_blob_name by default
            destination_file_name = source_blob_name

        destination_file_name = validate_path(destination_file_path) + str(source_blob_name)

        try:
            bucket = storage_client.get_bucket(bucket_name)
            blob = bucket.blob(source_blob_name)
            blob.download_to_filename(destination_file_name)
            logging.info('Blob {} downloaded to {}.'.format(source_blob_name, destination_file_name))
        except:
            logging.debug(
                'An error occurred during downloading blob {} from Google Cloud Storage'.format(source_blob_name))


    @staticmethod
    def validate_path(filepath):
    """Validate if the filepath ends with slash, if not, add the slash to the end."""
        if not str(filepath).endswith('/'):
            return str(filepath)+'/'
        return str(filepath)
