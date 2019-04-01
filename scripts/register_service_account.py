##!/usr/bin/env python

# This script was originally created in https://github.com/broadinstitute/firecloud-tools/tree/master/scripts/register_
# service_account. The primary reason that this was copied into this repo is because there was no reason to need the
# entire firecloud-tools repository for this one script. In addition, the use of the print statement in the original
# script did not work for the python 3 setup which was being used for the deployment

from argparse import ArgumentParser
from oauth2client.service_account import ServiceAccountCredentials
from firecloud import api as firecloud_api
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
    parser.add_argument(
        '-e',
        '--owner_email',
        dest='owner_email',
        action='store',
        required=True,
        help='Email address of the person who owns this service account',
    )
    parser.add_argument(
        '-u',
        '--url',
        dest='fc_url',
        action='store',
        default="https://api.firecloud.org",
        required=False,
        help='Base url of FireCloud server to contact (default https://api.firecloud.org)',
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
    headers = {"Authorization": "bearer " + bearer_token}
    print(bearer_token)

    headers["User-Agent"] = firecloud_api.FISS_USER_AGENT

    uri = args.fc_url + "/register/profile"

    profile_json = {
        "firstName": "None",
        "lastName": "None",
        "title": "None",
        "contactEmail": args.owner_email,
        "institute": "None",
        "institutionalProgram": "None",
        "programLocationCity": "None",
        "programLocationState": "None",
        "programLocationCountry": "None",
        "pi": "None",
        "nonProfitStatus": "false",
    }
    request = requests.post(uri, headers=headers, json=profile_json)

    print(request)

    if request.status_code == 200:
        print(
            """The service account {} is now registered with FireCloud.
               You can share workspaces with this address, or use it to call APIs.""".format(
                credentials._service_account_email
            )
        )
    else:
        print(format("Unable to register service account: {}", request.text))


if __name__ == "__main__":
    main()
