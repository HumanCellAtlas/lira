##!/usr/bin/env python
from argparse import ArgumentParser
from oauth2client.service_account import ServiceAccountCredentials
import requests.packages.urllib3

requests.packages.urllib3.disable_warnings()


def main():
    # The main argument parser
    parser = ArgumentParser(
        description="Register a service account for use in FireCloud."
    )

    # Core application arguments
    parser.add_argument(
        '-j',
        '--json_credentials',
        dest='json_credentials',
        action='store',
        required=True,
        help='Path to the json credentials file for this service account.',
    )

    args = parser.parse_args()

    scopes = [
        'https://www.googleapis.com/auth/userinfo.profile',
        'https://www.googleapis.com/auth/userinfo.email',
    ]
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        args.json_credentials, scopes=scopes
    )

    bearer_token = credentials.get_access_token().access_token
    print(bearer_token)


if __name__ == "__main__":
    main()
