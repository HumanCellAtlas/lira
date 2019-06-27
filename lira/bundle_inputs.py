import hashlib
from pipeline_tools.shared import metadata_utils, tenx_utils, http_requests


def get_hashes_from_file_manifest(file_manifest):
    """ Return a string that is a concatenation of the file hashes provided in the bundle manifest entry for a file:
        {sha1}{sha256}{s3_etag}{crc32c}
    """
    sha1 = file_manifest.sha1
    sha256 = file_manifest.sha256
    s3_etag = file_manifest.s3_etag
    crc32c = file_manifest.crc32c
    return '{sha1}{sha256}{s3_etag}{crc32c}'.format(sha1=sha1, sha256=sha256, s3_etag=s3_etag, crc32c=crc32c)


def get_smartseq2_workflow_input_hash(bundle):
    """ Return a string that is a concatenation of bundle-specific Smartseq2 paired-end workflow inputs:
        {sample_id}{taxon_id}{read_1}{read2}

        Where each "file hash" is a concatenation of {sha1}{sha256}{s3_etag}{crc32c}
    """
    sample_id = metadata_utils.get_sample_id(bundle)
    taxon_id = metadata_utils.get_sample_id(bundle)
    r1_manifest = [sf.manifest_entry for sf in bundle.sequencing_output if sf.read_index == 'read1']
    r2_manifest = [sf.manifest_entry for sf in bundle.sequencing_output if sf.read_index == 'read2']
    r1_hashes = get_hashes_from_file_manifest(r1_manifest[0])
    r2_hashes = get_hashes_from_file_manifest(r2_manifest[0])
    return bytes('{sample_id}{taxon_id}{read_1}{read_2}'.format(sample_id=sample_id,
                                                                taxon_id=taxon_id,
                                                                read_1=r1_hashes,
                                                                read_2=r2_hashes), encoding='utf8')


def get_optimus_workflow_input_hash(bundle):
    """ Return a string that is a concatenation of bundle-specific Optimus workflow inputs
    where the file hashes are for each set of read_1, read_2 and index_1 files in the order
    of their flow cell lane number. For example:
    {sample_id}{taxon_id}{lane1_r1}{lane1_r2}{lane1_i1}{lane2_r1}{lane2_r2}{lane2_i1}

    Each "file hash" is a concatenation of {sha1}{sha256}{s3_etag}{crc32c}
    """
    sample_id = metadata_utils.get_sample_id(bundle)
    taxon_id = metadata_utils.get_sample_id(bundle)
    inputs = '{sample_id}{taxon_id}'.format(sample_id=sample_id, taxon_id=taxon_id)
    fastq_files = [f for f in bundle.files.values() if str(f.format).lower() in ('fastq.gz', 'fastq')]
    fastq_dict = tenx_utils.create_fastq_dict(fastq_files)
    sorted_lanes = sorted(fastq_dict.keys(), key=int)
    for lane in sorted_lanes:
        r1_hashes = get_hashes_from_file_manifest(fastq_dict[lane]['read1'])
        r2_hashes = get_hashes_from_file_manifest(fastq_dict[lane]['read2'])
        file_hashes = '{0}{1}'.format(r1_hashes, r2_hashes)
        if fastq_dict[lane].get('index1'):
            i1_hashes = get_hashes_from_file_manifest(fastq_dict[lane]['index1'])
            file_hashes += i1_hashes
        inputs += file_hashes
    return bytes(inputs, encoding='utf8')


WORKFLOW_INPUTS = {
    'AdapterSmartSeq2SingleCell': get_smartseq2_workflow_input_hash,
    'AdapterOptimus': get_optimus_workflow_input_hash
}


def create_workflow_inputs_hash_label(workflow_name, bundle_id, bundle_version, dss_url):
    get_inputs_fn = WORKFLOW_INPUTS.get(workflow_name, None)
    if get_inputs_fn:
        bundle = metadata_utils.get_bundle_metadata(bundle_id, bundle_version, dss_url, http_requests.HttpRequests())
        workflow_inputs = get_inputs_fn(bundle)
        sha256_hash = hashlib.sha256(workflow_inputs)
        return {'hash-id': sha256_hash.hexdigest()}
