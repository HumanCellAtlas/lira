import hashlib
from pipeline_tools.pipelines.smartseq2 import smartseq2
from pipeline_tools.pipelines.optimus import optimus

WORKFLOW_INPUTS = {
    'AdapterSmartSeq2SingleCell': smartseq2.get_ss2_paired_end_inputs_to_hash,
    'AdapterOptimus': optimus.get_optimus_inputs_to_hash
}


def create_workflow_inputs_hash_label(workflow_name, bundle_id, bundle_version, dss_url):
    """
    Create a hash out of the bundle-specific inputs for a workflow.
    """
    get_inputs_to_hash = WORKFLOW_INPUTS.get(workflow_name, None)
    if get_inputs_to_hash:
        workflow_inputs = get_inputs_to_hash(bundle_id, bundle_version, dss_url)
        sha256_hash = hashlib.sha256(bytes(''.join(workflow_inputs), encoding='utf-8'))
        return {'hash-id': sha256_hash.hexdigest()}
