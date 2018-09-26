#!/usr/bin/env python
import sys
import time

import argparse
import base64
import functools
import json
import jwt
import requests
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime


def main(arguments=None):
    command, args = parser(arguments)

    # Get DCP authenticated header
    dcp_auth_client = DCPAuthClient(args['key_file'], args['google_project'])
    headers = dcp_auth_client.get_auth_header()
    args['headers'] = headers

    if command == 'create':
        create_subscription(args)
    elif command == 'list':
        list_subscription(args)
    elif command == 'delete':
        delete_subscription(args)


class DCPAuthClient(object):
    audience = "https://dev.data.humancellatlas.org/"

    def __init__(self, path_to_json_key, trusted_google_project):
        self.path_to_json_key = path_to_json_key
        self.trusted_google_project = trusted_google_project
        self.__token = None
        # TODO: check the liveness of the token and make it as singleton if applicable
        self.issue_time = None
        self.expire_time = None

    def get_auth_header(self):
        return {'Authorization': 'Bearer {}'.format(self.token)}

    @property
    def token(self):
        credentials = DCPAuthClient._from_json(self.path_to_json_key)
        tok = DCPAuthClient.get_service_jwt(service_credentials=credentials, audience=self.audience)
        self.verify_jwt(tok, audience=self.audience, trusted_google_project=self.trusted_google_project)
        return self.__token

    @staticmethod
    def _from_json(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)

    @staticmethod
    @functools.lru_cache(maxsize=32)
    def get_openid_config(openid_provider):
        res = requests.get("https://{}/.well-known/openid-configuration".format(openid_provider))
        res.raise_for_status()
        return res.json()

    @staticmethod
    def get_jwks_uri(openid_provider):
        if openid_provider.endswith("iam.gserviceaccount.com"):
            return "https://www.googleapis.com/service_accounts/v1/jwk/{}".format(openid_provider)
        else:
            return DCPAuthClient.get_openid_config(openid_provider)["jwks_uri"]

    @staticmethod
    @functools.lru_cache(maxsize=32)
    def get_public_keys(openid_provider):
        keys = requests.get(DCPAuthClient.get_jwks_uri(openid_provider)).json()["keys"]
        return {
            key["kid"]: rsa.RSAPublicNumbers(
                    e=int.from_bytes(base64.urlsafe_b64decode(key["e"] + "==="), byteorder="big"),
                    n=int.from_bytes(base64.urlsafe_b64decode(key["n"] + "==="), byteorder="big")
            ).public_key(backend=default_backend())
            for key in keys
        }

    @staticmethod
    def get_service_jwt(service_credentials, audience):
        iat = time.time()
        exp = iat + 3600
        payload = {'iss': service_credentials["client_email"],
                   'sub': service_credentials["client_email"],
                   'aud': audience,
                   'iat': iat,
                   'exp': exp,
                   'https://auth.data.humancellatlas.org/email': service_credentials["client_email"],
                   'https://auth.data.humancellatlas.org/group': 'hca',
                   'scope': ["openid", "email", "offline_access"]
                   }
        additional_headers = {'kid': service_credentials["private_key_id"]}
        signed_jwt = jwt.encode(payload, service_credentials["private_key"], headers=additional_headers,
                                algorithm='RS256').decode()
        return signed_jwt

    def verify_jwt(self, token, audience, trusted_google_project):
        assert token
        try:
            openid_provider = "humancellatlas.auth0.com"
            token_header = jwt.get_unverified_header(token)
            public_keys = DCPAuthClient.get_public_keys(openid_provider)
            tok = jwt.decode(token, key=public_keys[token_header["kid"]], audience=audience)
        except KeyError:
            unverified_token = jwt.decode(token, verify=False)
            issuer = unverified_token["iss"]
            assert issuer.endswith("@{}.iam.gserviceaccount.com".format(trusted_google_project))
            token_header = jwt.get_unverified_header(token)
            public_keys = DCPAuthClient.get_public_keys(issuer)
            tok = jwt.decode(token, key=public_keys[token_header["kid"]], audience=audience)
        self.__token = token
        self.issue_time = datetime.fromtimestamp(tok['iat']).strftime('%Y-%m-%d %H:%M:%S')
        self.expire_time = datetime.fromtimestamp(tok['exp']).strftime('%Y-%m-%d %H:%M:%S')


def create_subscription(args):
    print('Creating subscription in replica: {0} of DSS: {1}\n for {2}\n'.format(
            args['replica'],
            args['dss_url'],
            args['callback_base_url']))

    payload = _prep_json(
            callback_base_url=args['callback_base_url'],
            query_json_file=args['query_json'],
            query_param_token=args.get('query_param_token'),
            hmac_key_id=args.get('hmac_key_id'),
            hmac_key=args.get('hmac_key'),
            attachments_file=args['additional_metadata'])

    headers = args['headers']
    headers.update({'Content-type': 'application/json'})

    response = requests.put(url=args['dss_url'],
                            json=payload,
                            params={'replica': args['replica']},
                            headers=headers)
    response.raise_for_status()

    print('Successfully created a subscription!')
    print(response.json())


def _prep_json(callback_base_url, query_json_file, query_param_token, hmac_key_id, hmac_key, attachments_file):
    with open(query_json_file) as f:
        query = json.load(f)

    if hmac_key_id is not None:
        print('Subscribing with hmac key')
        payload = {
            'es_query': query,
            'callback_url': callback_base_url,
            'hmac_key_id': hmac_key_id,
            'hmac_secret_key': hmac_key
        }
    else:
        print('Subscribing with query param token')
        payload = {
            'es_query': query,
            'callback_url': '{0}?auth={1}'.format(callback_base_url, query_param_token)
        }

    if attachments_file:
        with open(attachments_file) as f:
            attachments = json.load(f)
        payload['attachments'] = attachments

    return payload


def list_subscription(args):
    print('Listing all subscriptions in replica: {0} of DSS: {1}\n'.format(
            args['replica'],
            args['dss_url']))

    response = requests.get(url=args['dss_url'],
                            params={'replica': args['replica']},
                            headers=args['headers'])
    response.raise_for_status()
    print(response.json())


def delete_subscription(args):
    url = '{dss_url}/{subscription_id}'.format(dss_url=args['dss_url'], subscription_id=args['subscription_id'])

    print('Delete the subscription {0} from replica: {1} of DSS: {2}\n'.format(
            args['subscription_id'],
            args['replica'],
            url))

    response = requests.delete(url=url,
                               params={'replica': args['replica']},
                               headers=args['headers'])
    response.raise_for_status()

    print('Successfully deleted the subscription.')
    print(response.json())


def parser(arguments):
    main_parser = argparse.ArgumentParser()

    subparsers = main_parser.add_subparsers(help='All available commands', dest='command')
    create = subparsers.add_parser('create', help='Create a new subscription in DSS.')
    delete = subparsers.add_parser('delete', help='Delete an existing subscription in DSS.')
    list = subparsers.add_parser('list', help='List all subscriptions in DSS.')

    # TODO rex: group sub-commands
    subscribe_sub_commands = (create, delete, list)

    # Add common arguments for all of the commands
    for sub_command in subscribe_sub_commands:
        sub_command.add_argument('--dss_url',
                                 help='URL to the HCA DCP Data Storage System API.',
                                 required=True)
        sub_command.add_argument('--key_file',
                                 help='JSON file containing Storage Service credentials.',
                                 required=True)
        sub_command.add_argument('--replica',
                                 help='Which replica to work on, use "gcp" by default. ["gcp", "aws"]',
                                 # required=True,
                                 default='gcp')
        sub_command.add_argument('--google_project',
                                 help='The google project the Lira is using.',
                                 required=True)

    # Add specific argument for `create` command
    create.add_argument('--callback_base_url',
                        help='Lira endpoint for receiving notifications.',
                        required=True)
    create.add_argument('--query_json',
                        help='JSON file containing the ElasticSearch Subscription query to register.',
                        required=True)

    HMAC_auth_group = create.add_mutually_exclusive_group(required=True)
    HMAC_auth_group.add_argument('--hmac_key', help='HMAC key.')
    HMAC_auth_group.add_argument('--query_param_token', help='Query param auth token.')

    create.add_argument('--hmac_key_id',
                        help='Unique identifier for HMAC key.')
    create.add_argument('--additional_metadata',
                        help='JSON file with additional fields to include in the notification.',
                        required=False,
                        default=None)

    # Add specific argument for `delete` command
    delete.add_argument('--subscription_id',
                        help='The subscription UUID to be deleted.',
                        required=True)

    # By default print out the help message for the script
    if len(arguments) == 0:
        arguments = ['-h']
    # By default print out the help message for sub commands
    if len(arguments) == 1:
        arguments = [arguments[0], '-h']

    args = vars(main_parser.parse_args(arguments))
    command = args['command']
    del args['command']

    # Make sure we are using the /subscriptions endpoint of DSS
    args['dss_url'] = '{url}/subscriptions'.format(url=args['dss_url'].strip('/'))

    return command, args


if __name__ == '__main__':
    main(sys.argv[1:])
