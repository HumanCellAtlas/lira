#!/usr/bin/env python
import argparse
import requests
import logging
from firecloud import api as firecloud_api
from oauth2client.service_account import ServiceAccountCredentials


def register_service_account(
    json_credentials,
    workflow_collection_id,
    firecloud_group_name,
    sam_url,
    firecloud_api_url,
):
    # Get bearer token from service account key. The bearer token has a max lifetime of one hour.
    # From https://github.com/broadinstitute/firecloud-tools/blob/master/scripts/register_service_account/register_service_account.py
    scopes = [
        'https://www.googleapis.com/auth/userinfo.profile',
        'https://www.googleapis.com/auth/userinfo.email',
    ]
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        json_credentials, scopes=scopes
    )
    headers = {"Authorization": "bearer " + credentials.get_access_token().access_token}
    headers["User-Agent"] = firecloud_api.FISS_USER_AGENT

    logging.info('Register service account in SAM')
    requests.post(sam_url + "/register/user", headers=headers)

    logging.info('Create new workflow-collection')
    workflow_collection_url = "{}/api/resource/workflow-collection/{}".format(
        sam_url, workflow_collection_id
    )
    requests.post(workflow_collection_url, headers=headers)

    logging.info('Create group in firecloud')
    firecloud_groups_url = "{}/api/groups/{}".format(
        firecloud_api_url, firecloud_group_name
    )
    response = requests.post(firecloud_groups_url, headers=headers)
    print(response)

    group_info = response.json()
    group_email = group_info['membersGroup']['groupEmail']

    logging.info('Add reader and writer policies to workflow collection')
    reader_policy = {"memberEmails": [], "actions": ["view"], "roles": ["reader"]}
    writer_policy = {
        "memberEmails": [group_email],
        "actions": ["view", "add", "delete", "abort"],
        "roles": ["writer"],
    }
    requests.put(
        workflow_collection_url + "/policies/reader",
        headers=headers,
        json=reader_policy,
    )
    requests.put(
        workflow_collection_url + "/policies/writer",
        headers=headers,
        json=writer_policy,
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--json_credentials',
        help='Path to the json credentials file for this service account.',
    )
    parser.add_argument(
        '--workflow_collection_id',
        help='Name of the workflow-collection to create in SAM.',
    )
    parser.add_argument(
        '--firecloud_group_name',
        help='Name of the user group to create in FireCloud to control workflow-collection permissions.',
    )
    parser.add_argument('--sam_url', help='SAM API url.')
    parser.add_argument('--firecloud_api_url', help='Firecloud API url.')
    args = parser.parse_args()
    register_service_account(
        json_credentials=args.json_credentials,
        workflow_collection_id=args.workflow_collection_id,
        firecloud_group_name=args.firecloud_group_name,
        sam_url=args.sam_url,
        firecloud_api_url=args.firecloud_api_url,
    )
