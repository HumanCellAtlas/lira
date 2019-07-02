import hashlib
import unittest
from unittest import mock
from lira import bundle_inputs
from pipeline_tools.shared.metadata_utils import get_hashes_from_file_manifest
from humancellatlas.data.metadata.api import ManifestEntry


class TestGetBundleInputs(unittest.TestCase):

    def setUp(self):
        self.workflow_name = 'AdapterSmartSeq2SingleCell'
        self.sample_id = 'sample_id'
        self.taxon_id = 'taxon_id'
        self.fastq1_manifest = ManifestEntry(url='gs://foo/read1.fastq',
                                             sha1='sha1_read1',
                                             sha256='sha256_read1',
                                             s3_etag='s3_etag_read1',
                                             crc32c='crc32c_read1',
                                             uuid='1',
                                             version='v1',
                                             size='100',
                                             name='read1.fastq',
                                             indexed=True,
                                             content_type='fastq')
        self.fastq2_manifest = ManifestEntry(url='gs://foo/read2.fastq',
                                             sha1='sha1_read2',
                                             sha256='sha256_read2',
                                             s3_etag='s3_etag_read2',
                                             crc32c='crc32c_read2',
                                             uuid='2',
                                             version='v1',
                                             size='100',
                                             name='read2.fastq',
                                             indexed=True,
                                             content_type='fastq')

    @mock.patch('pipeline_tools.pipelines.smartseq2.smartseq2.get_ss2_paired_end_inputs')
    def test_create_workflow_inputs_hash_label(self, mock_hash):
        expected_inputs = (self.sample_id, self.taxon_id, self.fastq1_manifest, self.fastq2_manifest)
        mock_hash.return_value = expected_inputs
        workflow_hash = bundle_inputs.create_workflow_inputs_hash_label(workflow_name=self.workflow_name,
                                                                        bundle_id='fake_id',
                                                                        bundle_version='fake_version',
                                                                        dss_url='https://fake-url.org')
        r1_file_hashes = get_hashes_from_file_manifest(self.fastq1_manifest)
        r2_file_hashes = get_hashes_from_file_manifest(self.fastq2_manifest)
        expected_hash = hashlib.sha256(bytes(f'{self.sample_id}{self.taxon_id}{r1_file_hashes}{r2_file_hashes}',
                                             encoding='utf-8'))
        self.assertEquals(workflow_hash['hash-id'], expected_hash.hexdigest())
