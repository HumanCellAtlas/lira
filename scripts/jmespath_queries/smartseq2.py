subscription_query = (
    "(files.library_preparation_protocol_json[].library_construction_method[].ontology | contains(@, `EFO:0008931`))"
    "&& (files.sequencing_protocol_json[].paired_end | [0])"
    "&& files.donor_organism_json[].biomaterial_core.ncbi_taxon_id[] | (min(@) == `9606` && max(@) == `9606`)"
    "&& files.sequencing_protocol_json[].sequencing_approach.ontology_label | not_null(@, `[]`) | !contains(@, `CITE-seq`)"
    "&& files.analysis_process_json[].process_type.text | not_null(@, `[]`) | !contains(@, `analysis`)"
)
