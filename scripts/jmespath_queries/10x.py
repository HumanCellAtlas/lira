subscription_query = (
    "(files.library_preparation_protocol_json[].library_construction_method[].ontology_label | contains(@, `10X v2 sequencing`))"
    "&& (files.library_preparation_protocol_json[].end_bias | contains(@, `3 prime tag`))"
    "&& (files.library_preparation_protocol_json[].nucleic_acid_source | contains(@, `single cell`))"
    "&& files.donor_organism_json[].biomaterial_core.ncbi_taxon_id[] | (min(@) == `9606` && max(@) == `9606`)"
    "&& files.sequencing_protocol_json[].sequencing_approach.ontology_label | not_null(@, `[]`) | !contains(@, `CITE-seq`)"
    "&& files.donor_organism_json[].biomaterial_core.ncbi_taxon_id | not_null(@, `[]`) | !contains(@, `analysis`)"
)
