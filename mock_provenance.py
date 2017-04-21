#!/usr/bin/env python

import argparse
import json
import os.path

BUNDLE_ID_VERSION = "bluebox://43bd7eb0-23a3-4898-b043-f7e982de281a/v1/05bd7eb0-23a3-4898-b043-f7e982de281g/v1/"


class Provenance:

    ANALYSIS_ID = "analysis_id"
    BAM = "aligned_bam"
    CHECKSUM = "checksum"
    EXPRESSION = "expression_matrix"
    FORMAT = "format"
    INPUTS = "inputs"
    LEFT_SAMPLE = "left_sample"
    LOG = "log"
    METHOD = "computational_method"
    OUTPUT = "outputs"
    PATH = "file_path"
    REFERENCE = "reference_version"
    RIGHT_SAMPLE = "right_sample"
    SAMPLE = "sample_json"
    SCHEMA = "metadata_schema"
    START_STEP = "start_utc"
    STEP_ALIGN = "step_align"
    STEP_UPLOAD ="step_upload"
    STOP_STEP = "stop_utc"
    TIME_START = "timestamp_start_utc"
    TIME_STOP = "timestamp_stop_utc"
    TIMING = "timings"
    QC = "report_qc"


    def __init__(self):

        self.mock_checksum = "d0f7d08f1980f7980f"
        self.start = "2017-05-18T03:44:23-5:00"
        self.stop = "2017-05-18T014:44:23-5:00"
        self.id = "4342342"
        self.schema_version = "version_232"


        self.json = { Provenance.TIME_START : self.start,
                      Provenance.TIME_STOP : self.stop,
                      Provenance.ANALYSIS_ID : self.id,
                      Provenance.SCHEMA : self.schema_version,
                      Provenance.TIMING : {},
                      Provenance.INPUTS : [],
                      Provenance.OUTPUT : []}

        #Add fake timings for some steps.
        self.add_step(Provenance.STEP_UPLOAD)
        self.add_step(Provenance.STEP_ALIGN)


    def add_input_file(self, name, input_file, file_type):
        new_file = self.get_file_json(name, input_file, file_type)
        self.json[Provenance.INPUTS].append(new_file)


    def add_reference(self, reference_file):
        self.json[Provenance.REFERENCE] = reference_file

    def add_sample_json(self, json_file):
        self.json[Provenance.SAMPLE] = json_file


    def add_computational_method(self, method_uri):
        self.json[Provenance.METHOD] = method_uri


    def add_log(self, log_file):
        self.json[Provenance.LOG] = log_file


    def add_output(self, name, output_file, file_type):
        new_file = self.get_file_json(name, output_file, file_type)
        self.json[Provenance.OUTPUT].append(new_file)


    def add_step(self, step_name):
        new_step = { step_name : {Provenance.START_STEP : self.start,
                                  Provenance.STOP_STEP : self.stop}}
        self.json[Provenance.TIMING].update(new_step)


    def get_file_json(self, name, file_path, file_type):
        return({name: {Provenance.CHECKSUM: self.mock_checksum,
                       Provenance.PATH: file_path,
                       Provenance.FORMAT: file_type}})


    def write_to_file(self, write_file):
        with open(write_file, "w") as json_wrtr:
            json_wrtr.write(json.dumps(self.json,
                             sort_keys=True,
                             indent = 4,
                             separators=(",", ": ")))


# Start script
# Parse args
# Make JSON object and dump to file.
argument_prsr = argparse.ArgumentParser(
            prog=os.path.basename(__file__),
            description="Mocks a provenance json",
            conflict_handler="resolve")

# Write file
write_help = "File to write the provenance.json."
argument_prsr.add_argument(
                         dest="write_file",
                         help=write_help)

# Analysis inputs
## Input Left
left_help = "Left Fastq file used in analysis."
left_default = "smartseq1.fastq.gz"
argument_prsr.add_argument("--left_fastq",
                         default=left_default,
                         dest="pipe_left",
                         help=left_help)

## Input right
right_help = "Right fastq file used in analysis."
right_default = "smartseq2.fastq.gz"
argument_prsr.add_argument("--right_fastq",
                         default=right_default,
                         dest="pipe_right",
                         help=right_help)

## Sample JSON
sample_help = "Sample metadata from ingest bundle."
sample_default = "sample.json"
argument_prsr.add_argument("--sample_json",
                         default=sample_default,
                         dest="sample_json",
                         help=sample_help)

## Method
method_help = "Computational method ran as analysis."
method_default = "".join(["https://www.dockstore.org:8443/api/ga4gh/v1/tools/quay.io%2Fhca%2Fdockstore-hca-uploader/"])
argument_prsr.add_argument("--method_uri",
                         default=method_default,
                         dest="pipe_method",
                         help=method_help)

## Reference
reference_help = "Reference directory used in analysis."
reference_default = "hg_19.fasta"
argument_prsr.add_argument("--reference_dir",
                         default=reference_default,
                         dest="pipe_ref",
                         help=reference_help)

# Analysis outputs
## bam
bam_help = "Bam generated from analysis."
bam_default = "smartseq2.bam"
argument_prsr.add_argument("--bam",
                         default=bam_default,
                         dest="pipe_bam",
                         help=bam_help)

## expression
expression_help = "Expression matrix generated from analysis."
expression_default = "smartseq2_expression.txt"
argument_prsr.add_argument("--expression",
                         default=expression_default,
                         dest="pipe_exp",
                         help=expression_help)

## log
log_help = "Log detailing analysis."
log_default = "smartseq2_log.tar.gz"
argument_prsr.add_argument("--log",
                         default=log_default,
                         dest="pipe_log",
                         help=log_help)

## QC
qc_help = "Quality control matrix generated from analysis."
qc_default = "smartseq2_qc.txt"
argument_prsr.add_argument("--qc",
                         default=qc_default,
                         dest="pipe_qc",
                         help=qc_help)

args = argument_prsr.parse_args()


prov_json = Provenance()
prov_json.add_input_file("left_sample", BUNDLE_ID_VERSION + args.pipe_left, "fastq.gz")
prov_json.add_input_file("right_sample", BUNDLE_ID_VERSION + args.pipe_right, "fastq.gz")
prov_json.add_reference(BUNDLE_ID_VERSION + args.pipe_ref)
prov_json.add_computational_method(args.pipe_method)
prov_json.add_log(BUNDLE_ID_VERSION + args.pipe_log)
prov_json.add_sample_json(BUNDLE_ID_VERSION + args.sample_json)
prov_json.add_output("aligned_bam", BUNDLE_ID_VERSION + args.pipe_bam, "bam")
prov_json.add_output("expression_matrix", BUNDLE_ID_VERSION + args.pipe_exp, "expression_matrix")
prov_json.add_output("report_qc", BUNDLE_ID_VERSION + args.pipe_qc, "qc_matrix")
prov_json.write_to_file(args.write_file)




