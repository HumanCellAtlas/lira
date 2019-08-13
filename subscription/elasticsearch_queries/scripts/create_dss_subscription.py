# Script to generate the portion of the DSS subscription via ElasticSearch query based on the last known schema
# versions that Secondary Analysis is compatible with including compatibility dependencies on Metadata API.

from enum import Enum


class MetadataSchemaName(Enum):
    DONOR_ORGANISM = "donor_organism"
    SPECIMEN_FROM_ORGANISM = "specimen_from_organism"
    CELL_SUSPENSION = "cell_suspension"
    CELL_LINE = "cell_line"
    ORGANOID = "organoid"
    IMAGED_SPECIMEN = "imaged_specimen"
    REFERENCE_FILE = "reference_file"
    SEQUENCE_FILE = "sequence_file"
    SUPPLEMENTARY_FILE = "supplementary_file"
    IMAGE_FILE = "image_file"
    PROTOCOL = "protocol"
    AGGREGATE_GENERATION_PROTOCOL = "aggregate_generation_protocol"
    COLLECTION_PROTOCOL = "collection_protocol"
    DIFFERENTIATION_PROTOCOL = "differentiation_protocol"
    DISSOCIATION_PROTOCOL = "dissociation_protocol"
    ENRICHMENT_PROTOCOL = "enrichment_protocol"
    IPSC_INDUCTION_PROTOCOL = "ipsc_induction_protocol"
    IMAGING_PROTOCOL = "imaging_protocol"
    LIBRARY_PREPARATION_PROTOCOL = "library_preparation_protocol"
    SEQUENCING_PROTOCOL = "sequencing_protocol"
    IMAGING_PREPARATION_PROTOCOL = "imaging_preparation_protocol"
    PROJECT = "project"
    PROCESS = "process"
    DISSOCIATION_PROCESS = "dissociation_process"
    ENRICHMENT_PROCESS = "enrichment_process"
    LIBRARY_PREPARATION_PROCESS = "library_preparation_process"
    SEQUENCING_PROCESS = "sequencing_process"


LATEST_SUPPORTED_MD_SCHEMA_VERSIONS = {
    MetadataSchemaName.DONOR_ORGANISM: {
        'major': 15,
        'minor': 3
    },

    MetadataSchemaName.SPECIMEN_FROM_ORGANISM: {
        'major': 10,
        'minor': 2
    },

    MetadataSchemaName.CELL_SUSPENSION: {
        'major': 13,
        'minor': 1
    },

    MetadataSchemaName.CELL_LINE: {
        'major': 14,
        'minor': 3
    },

    MetadataSchemaName.ORGANOID: {
        'major': 11,
        'minor': 1
    },

    MetadataSchemaName.IMAGED_SPECIMEN: {
        'major': 3,
        'minor': 1
    },

    MetadataSchemaName.REFERENCE_FILE: {
        'major': 3,
        'minor': 1
    },

    MetadataSchemaName.SEQUENCE_FILE: {
        'major': 9,
        'minor': 1
    },

    MetadataSchemaName.SUPPLEMENTARY_FILE: {
        'major': 2,
        'minor': 1
    },

    MetadataSchemaName.IMAGE_FILE: {
        'major': 2,
        'minor': 1
    },

    MetadataSchemaName.PROTOCOL: {
        'major': 7,
        'minor': 0
    },

    MetadataSchemaName.AGGREGATE_GENERATION_PROTOCOL: {
        'major': 2,
        'minor': 0
    },

    MetadataSchemaName.COLLECTION_PROTOCOL: {
        'major': 9,
        'minor': 1
    },

    MetadataSchemaName.DIFFERENTIATION_PROTOCOL: {
        'major': 2,
        'minor': 1
    },

    MetadataSchemaName.DISSOCIATION_PROTOCOL: {
        'major': 6,
        'minor': 1
    },

    MetadataSchemaName.ENRICHMENT_PROTOCOL: {
        'major': 3,
        'minor': 0
    },

    MetadataSchemaName.IPSC_INDUCTION_PROTOCOL: {
        'major': 3,
        'minor': 1
    },

    MetadataSchemaName.IMAGING_PROTOCOL: {
        'major': 11,
        'minor': 1
    },

    MetadataSchemaName.LIBRARY_PREPARATION_PROTOCOL: {
        'major': 6,
        'minor': 1
    },

    MetadataSchemaName.SEQUENCING_PROTOCOL: {
        'major': 10,
        'minor': 0
    },

    MetadataSchemaName.IMAGING_PREPARATION_PROTOCOL: {
        'major': 2,
        'minor': 1
    },

    MetadataSchemaName.PROJECT: {
        'major': 9,
        'minor': 0
    },

    MetadataSchemaName.PROCESS: {
        'major': 9,
        'minor': 1
    },

    MetadataSchemaName.DISSOCIATION_PROCESS: {
        'major': 5,
        'minor': 1
    },

    MetadataSchemaName.ENRICHMENT_PROCESS: {
        'major': 5,
        'minor': 1
    },

    MetadataSchemaName.LIBRARY_PREPARATION_PROCESS: {
        'major': 5,
        'minor': 1
    },

    MetadataSchemaName.SEQUENCING_PROCESS: {
        'major': 5,
        'minor': 1
    }
}


def generate_elastic_search_query_for_schema_versions():
    for schema_name in LATEST_SUPPORTED_MD_SCHEMA_VERSIONS:
        print("""
{
    "bool": {
      "should": [
        {
          "bool": {
            "must": [
              {
                "term": {
                  "files.%s_json.provenance.schema_major_version": %d
                }
              }
            ]
          }
        }
      ],
      "minimum_should_match": 1
    }
  },
            """ % (schema_name.value, LATEST_SUPPORTED_MD_SCHEMA_VERSIONS[schema_name]['major']))


generate_elastic_search_query_for_schema_versions()
