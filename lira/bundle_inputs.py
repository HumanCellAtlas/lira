import hashlib
from pipeline_tools.shared import metadata_utils, tenx_utils, http_requests


def get_smartseq2_workflow_inputs(bundle):
    """ Return a string that is a concatenation of bundle-specific Smartseq2 paired-end workflow inputs:
        {sample_id}{taxon_id}{read_1_sha256}{read2_sha256}
    """
    sample_id = metadata_utils.get_sample_id(bundle)
    taxon_id = metadata_utils.get_sample_id(bundle)
    read_1_sha = [sf.manifest_entry.sha256 for sf in bundle.sequencing_output if sf.read_index == 'read1']
    read_2_sha = [sf.manifest_entry.sha256 for sf in bundle.sequencing_output if sf.read_index == 'read2']
    return bytes('{sample_id}{taxon_id}{read_1}{read_2}'.format(sample_id=sample_id,
                                                                taxon_id=taxon_id,
                                                                read_1=read_1_sha[0],
                                                                read_2=read_2_sha[0]), encoding='utf8')


def get_optimus_workflow_inputs(bundle):
    sample_id = metadata_utils.get_sample_id(bundle)
    taxon_id = metadata_utils.get_sample_id(bundle)
    inputs = '{sample_id}{taxon_id}'.format(sample_id=sample_id, taxon_id=taxon_id)
    fastq_files = [f for f in bundle.files.values() if str(f.format).lower() in ('fastq.gz', 'fastq')]
    fastq_dict = tenx_utils.create_fastq_dict(fastq_files)
    for lane in fastq_dict:
        file_hashes = '{0}{1}'.format(fastq_dict[lane]['read1']['sha256'], fastq_dict[lane]['read2']['sha256'])
        if fastq_dict[lane].get('index1'):
            file_hashes += fastq_dict[lane]['index1']['sha256']
        inputs += file_hashes
    return bytes(inputs)


# what if inputs change in a newer version?
WORKFLOW_INPUTS = {'AdapterSmartSeq2SingleCell': get_smartseq2_workflow_inputs,
                   'AdapterOptimus': get_optimus_workflow_inputs}


def create_workflow_inputs_hash_label(workflow_name, bundle_id, bundle_version, dss_url):
    get_inputs_fn = WORKFLOW_INPUTS.get(workflow_name, None)
    if get_inputs_fn:
        bundle = metadata_utils.get_bundle_metadata(bundle_id, bundle_version, dss_url, http_requests.HttpRequests())
        workflow_inputs = get_inputs_fn(bundle)
        sha256_hash = hashlib.sha256(workflow_inputs)
        return {'workflow-hash': sha256_hash.hexdigest()}
