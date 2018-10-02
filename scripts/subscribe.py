#!/usr/bin/env python
import sys

import argparse
import json
import requests

try:
    from DCPAuthClient import DCPAuthClient
except ModuleNotFoundError:
    print('Cannot find the DCPAuthClient within this folder!')
    exit(1)


def main(arguments=None):
    command, args = parser(arguments)

    # Get DCP authenticated header
    dcp_auth_client = DCPAuthClient(args['key_file'], args['google_project'])
    headers = dcp_auth_client.get_auth_header()
    args['headers'] = headers

    if command == 'create':
        create_subscription(args)
    elif command == 'get':
        get_subscriptions(args)
    elif command == 'delete':
        delete_subscription(args)


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
    print(json.dumps(response.json(), indent=4))


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


def get_subscriptions(args):
    print('Listing all subscriptions in replica: {0} of DSS: {1}\n'.format(
            args['replica'],
            args['dss_url']))

    response = requests.get(url=args['dss_url'],
                            params={'replica': args['replica']},
                            headers=args['headers'])
    response.raise_for_status()
    print(json.dumps(response.json(), indent=4))


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
    print(json.dumps(response.json(), indent=4))


def parser(arguments):
    main_parser = argparse.ArgumentParser()

    subparsers = main_parser.add_subparsers(help='All available commands', dest='command')
    create = subparsers.add_parser('create', help='Create a new subscription in DSS.')
    delete = subparsers.add_parser('delete', help='Delete an existing subscription in DSS.')
    get = subparsers.add_parser('get', help='Get and list all subscriptions in DSS.')

    # TODO rex: group sub-commands
    subscribe_sub_commands = (create, delete, get)

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
    main(sys.argv[1:])  # exclude the python file name from the input arguments
