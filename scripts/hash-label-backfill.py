"""
This script is designed for updating the `hash-id` label for the
existing workflows in Cromwell. It will compute the hash value by
looking into the bundles and caculate the fields that are part of
the pipeline inputs.

We're keeping this script in lira/scripts as it is intended to
be a one-time backfill. To run the script, however, first copy
it into lira/lira and run it from there so that it has access
to lira's package structure.

Note the run time of this script can be up to a few days, depending
on the number of the workflows it has to look at and compute.

An example invocation is:

```
python hash-label-backfill.py -v 2 \
                             -k caas_key.json \
                             -e staging -p 00000000-0000-0000-0000-000000000000 \
                             -l '{"workflow-name":"AdapterOptimus"}' \
                             --save-log
```
-------- Operation Records --------
2019/12/05  backfill_version: "2"

-----------------------------------
"""
import argparse
import json
import bundle_inputs
from cromwell_tools.cromwell_api import CromwellAPI
from cromwell_tools.cromwell_auth import CromwellAuth
from datetime import datetime
from tqdm import tqdm
import sys
import requests


DSS_URL = {
    "prod": "https://dss.data.humancellatlas.org/v1",
    "staging": "https://dss.staging.data.humancellatlas.org/v1",
    "int": "https://dss.integration.humancellatlas.org/v1",
}


def get_project_workflows(
    project_uuid: str,
    auth: "CromwellAuth",
    required_labels: dict = None,
    backfill_version: int = None,
    save_log: bool = False,
) -> list:
    """Get a list of the workflows need to be updated by `project_uuid`.
    Note it will skip the workflows that don't have the labels specified
    by `required_labels` if applicable. Log dumping is optional."""
    label_dict = required_labels or {}
    label_dict["project_uuid"] = project_uuid
    query_dict = {"label": label_dict, "additionalQueryResultFields": "labels"}
    response = CromwellAPI.query(query_dict, auth, raise_for_status=True)

    target_workflows = [
        workflow
        for workflow in response.json()["results"]
        if workflow["labels"].get("backfill_version", None) != backfill_version
    ]

    if save_log:
        with open(
            f"backfill-{datetime.utcnow().strftime('%Y-%m-%dT%H-%M-%S')}.json", "w"
        ) as fp:
            json.dump(target_workflows, fp)
    return target_workflows


def label_workflow_with_hash(
    workflow: dict, env: str, auth: "CromwellAuth", backfill_version: str = None
) -> "requests.Response":
    """Compute the hash and send a PATCH /label request to Cromwell. Also add
    an additional `backfill_version` flag to the patched workflows if applicable."""
    hash_label = bundle_inputs.get_workflow_inputs_to_hash(
        workflow["labels"]["workflow-name"],
        workflow["labels"]["bundle-uuid"],
        workflow["labels"]["bundle-version"],
        DSS_URL[env],
    )
    if backfill_version:
        hash_label["backfill_version"] = backfill_version
    return CromwellAPI.patch_labels(workflow["id"], labels=hash_label, auth=auth)


def patch_workflows(
    workflows: dict, env: str, auth: "CromwellAuth", backfill_version: str = None
) -> None:
    """The entrypoint fo the script, patching the workflows."""
    results = [
        (
            workflow["id"],
            label_workflow_with_hash(
                workflow=workflow, env=env, auth=auth, backfill_version=backfill_version
            ),
        )
        for workflow in tqdm(workflows)
    ]
    print("Successfully patched workflows:")
    [print(wfid) for wfid, result in results if result.status_code == 200]
    print("Failed to patch workflows:")
    [print(wfid) for wfid, result in results if result.status_code != 200]


class DefaultHelpParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write("error: %s\n" % message)
        self.print_help()
        sys.exit(2)


if __name__ == "__main__":
    parser = DefaultHelpParser(
        description="Command Line Interface for backfilling existing workflows with hash labels for HCA projects.",
        prog="hash label backfiller",
    )
    parser.add_argument(
        "-l",
        "--required-labels",
        dest="required_labels",
        metavar="",
        help="Only backfill worfklows with these labels.",
    )
    parser.add_argument(
        "--save-log",
        dest="save_log",
        action="store_true",
        help="Only backfill worfklows with these labels.",
    )
    parser.add_argument(
        "-v",
        "--backfill-version",
        dest="backfill_version",
        metavar="",
        type=str,
        help="Only backfill workflows that without the version this flag indicates.",
    )
    parser.add_argument(
        "-k",
        "--caas-key",
        dest="caas_key",
        metavar="",
        help="Service account key json for caas.",
        required=True,
    )
    parser.add_argument(
        "-e",
        "--environment",
        dest="env",
        metavar="",
        help="DSS environment that the project bundles exist in (one of prod, staging, int).",
        required=True,
    )
    either = parser.add_mutually_exclusive_group(required=True)
    either.add_argument(
        "-p",
        "--project-uuid",
        dest="project_uuid",
        metavar="",
        help="Project uuid of the workflows to backfill.",
    )
    either.add_argument(
        "-f",
        "--file",
        dest="file",
        metavar="",
        help="File containing new-line seprarted project uuids of workflows to backfill.",
    )
    args = parser.parse_args()

    cromwell_auth = CromwellAuth.harmonize_credentials(
        url="https://cromwell.caas-prod.broadinstitute.org",
        service_account_key=args.caas_key,
    )
    if args.required_labels:
        required_labels = json.loads(args.required_labels)
    else:
        required_labels = None

    if args.project_uuid:
        workflows = get_project_workflows(
            project_uuid=args.project_uuid,
            auth=cromwell_auth,
            required_labels=required_labels,
            backfill_version=args.backfill_version,
            save_log=args.save_log,
        )
    else:
        with open(args.file, "r") as f:
            workflows = [
                workflow
                for line in f
                for workflow in get_project_workflows(
                    line.strip(),
                    cromwell_auth,
                    required_labels,
                    args.backfill_version,
                    args.save_log,
                )
            ]

    patch_workflows(workflows, args.env, cromwell_auth, args.backfill_version)
