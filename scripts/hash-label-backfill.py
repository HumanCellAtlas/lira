import argparse
import json
from lira import bundle_inputs
from cromwell_tools.cromwell_api import CromwellAPI
from cromwell_tools.cromwell_auth import CromwellAuth

def get_project_workflows(project_uuid, auth, required_labels=None):
    label_dict = required_labels or {}
    label_dict['project_uuid'] = project_uuid
    query_dict = {
        'label': label_dict,
        'additionalQueryResultFields': 'labels',
    }
    response = CromwellAPI.query(query_dict, auth, raise_for_status=True)
    return [
        workflow for workflow in response.json()['results'] 
        if 'hash-id' not in workflow['labels']
    ]

def label_workflow_with_hash(workflow, auth):
    hash_label = bundle_inputs.get_workflow_inputs_to_hash(
        workflow['labels']['workflow-name'],
        workflow['labels']['bundle-uuid'],
        workflow['labels']['bundle-version'],
        'https://dss.data.humancellatlas.org/v1',
    )
    return CromwellAPI.patch_labels(
        workflow['id'],
        labels=hash_label,
        auth=auth,
    )
    
def patch_workflows(workflows, auth)
    results = [
        (workflow['id'], label_workflow_with_hash(workflow, auth))
        for workflow in workflows
    ]
    print('Successfully patched workflows:')
    [print(wfid) for wfid, result in results if result.status_code == 200]
    print('Failed to patch workflows:')
    [print(wfid) for wfid, result in results if result.status_code != 200]

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--required_labels', dest='required_labels', 'only backfill worfklows with these labels')
    parser.add_argument('-k', '--caas_key', dest='caas_key', 'service account key json for caas', required=True)
    either = parser.add_mutually_exclusive_group(required=True)
    either.add_argument('-p', '--project_uuid', dest='project_uuid', 'project uuid of the workflows to backfill')
    either.add_argument('-f', '--file', dest='file', 'file containing new-line seprarted project uuids of workflows to backfill')
    
    cromwell_auth = CromwellAuth.harmonize_credentials(
        url='https://cromwell.caas-prod.broadinstitute.org',
        service_account_key=args.caas_key
    )
    if args.required_labels:
        required_labels = json.loads(args.required_labels)
    else:
        required_labels = None
    
    if args.project_uuid:
        workflows = get_project_workflows(args.project_uuid, cromwell_auth, required_labels)
    else:
        with open(file, 'r') as f:
            workflows = [
                workflow
                for workflow in
                get_project_workflows(line.strip(), cromwell_auth, required_labels)
                for line in f
            ]
            
    patch_workflows(workflows, cromwell_auth)
