import argparse
import logging
import requests
from cromwell_tools import cromwell_tools


def get_workflows(cromwell_url, query_dict, caas_key):
    response = cromwell_tools.query_workflows(cromwell_url, query_dict, caas_key=caas_key)
    workflows = response.json()['results']
    return workflows


def abort_workflows(cromwell_url, workflows, caas_key, dry_run=False):
    auth, headers = cromwell_tools._get_auth_credentials(caas_key=caas_key)
    logging.info('Aborting {} workflows in {}'.format(len(workflows), cromwell_url))
    for workflow in workflows:
        workflow_id = workflow['id']
        abort_url = '{}/api/workflows/v1/{}/abort'.format(cromwell_url, workflow_id)
        if not dry_run:
            response = requests.post(abort_url, auth=auth, headers=headers)
            if response.status_code != 200:
                logging.info('Could not abort workflow {}'.format(workflow_id))
        logging.info('Aborted workflow {}'.format(workflow_id))


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument('--cromwell_url')
    parser.add_argument('--caas_key')
    parser.add_argument('--dry_run', default='false')
    args = parser.parse_args()
    query_dict = {
        'status': ['On Hold', 'Running']
    }
    dry_run = True if args.dry_run.lower() == 'true' else False
    target_workflows = get_workflows(args.cromwell_url, query_dict, args.caas_key)
    abort_workflows(args.cromwell_url, target_workflows, args.caas_key, dry_run=dry_run)
