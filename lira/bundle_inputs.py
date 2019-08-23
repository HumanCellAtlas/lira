import hashlib
from pipeline_tools.pipelines.smartseq2 import smartseq2
from pipeline_tools.pipelines.optimus import optimus

WORKFLOW_INPUTS = {
    'AdapterSmartSeq2SingleCell': smartseq2.get_ss2_paired_end_inputs_to_hash,
    'AdapterOptimus': optimus.get_optimus_inputs_to_hash,
}


def get_workflow_inputs_to_hash(workflow_name, bundle_id, bundle_version, dss_url):
    """
    Get the bundle-specific inputs for a workflow.

    Args:
        workflow_name (str): The name of the WDL workflow
        bundle_id (str): The UUID of the HCA data bundle
        bundle_version (str): The version timestamp of the HCA data bundle
        dss_url (str): The URL to a particular HCA Data Store environment

    Returns:
        dict: A dictionary of {'hash-id': <SHA-256 hexadecimal hash>}
    """
    get_inputs_to_hash = WORKFLOW_INPUTS.get(workflow_name, None)
    if get_inputs_to_hash:
        workflow_inputs = get_inputs_to_hash(bundle_id, bundle_version, dss_url)
        workflow_inputs_hash = get_hash_id(workflow_inputs)
        return {'hash-id': workflow_inputs_hash}


def get_hash_id(workflow_inputs):
    """
    Create a SHA-256 hash of the values in workflow_inputs.

    Args:
        workflow_inputs (tuple): Tuple of bundle-specific inputs to the workflow

    Returns:
        str: SHA-256 hexadecimal hash
    """
    sha256_hash = hashlib.sha256(
        bytes(''.join((str(i) for i in workflow_inputs)), encoding='utf-8')
    )
    return sha256_hash.hexdigest()
