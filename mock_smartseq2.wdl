task get_inputs {
  String bundle_uuid
  String bundle_version

  command <<<
    python <<CODE
    import json
    import requests
    import subprocess

    uuid = '${bundle_uuid}'
    version = '${bundle_version}'
    print('Getting bundle manifest for id {0}, version {1}'.format(uuid, version))

    url = "https://hca-dss.czi.technology/v1/bundles/" + uuid + "?replica=aws"
    print('GET {0}'.format(url))
    response = requests.get(url)
    print('{0}'.format(response.status_code))
    print('{0}'.format(response.text))
    manifest = response.json()

    bundle = manifest['bundle']
    for f in bundle['files']:
        if f['name'] == 'assay.json':
            print('Downloading assay.json')
            assay_json_uuid = f['uuid']
            url = "https://hca-dss.czi.technology/v1/files/" + assay_json_uuid + "?replica=aws" 
            print('GET {0}'.format(url))
            response = requests.get(url)
            print('{0}'.format(response.status_code))
            print('{0}'.format(response.text))
            assay_json = response.json()

    left_fastq_name = None
    right_fastq_name = None
    for f in assay_json['files']:
        if f['format'] == '.fastq.gz' and f['type'] == 'read1':
            left_fastq_name = f['name']
        if f['format'] == '.fastq.gz' and f['type'] == 'read2':
            right_fastq_name = f['name']

    file_uuids = {}
    for f in bundle['files']:
      if f['name'] == left_fastq_name:
          file_uuids['left_fastq'] = f['uuid']
      if f['name'] == right_fastq_name:
          file_uuids['right_fastq'] = f['uuid']

    print('Creating input map')
    with open('inputs.tsv', 'w') as f:
        f.write('{0}\t{1}\n'.format(file_uuids['left_fastq'], left_fastq_name))
        f.write('{0}\t{1}'.format(file_uuids['right_fastq'], right_fastq_name))
    print('Wrote input map')
    CODE
  >>>
  runtime {
    docker: "gcr.io/broad-dsde-mint-dev/aws"
  }
  output {
    Array[Array[String]] inputs = read_tsv("inputs.tsv")
  }
}

task localize {
  String left_fastq_uuid
  String right_fastq_uuid
  String left_fastq_name
  String right_fastq_name
  String dollar='$'

  command <<<
    echo "Copying inputs"
    echo "Copying ${left_fastq_name}"
    curl -L "https://hca-dss.czi.technology/v1/files/${left_fastq_uuid}?replica=aws" > ${left_fastq_name}
    echo "Copying ${right_fastq_name}"
    curl -L "https://hca-dss.czi.technology/v1/files/${right_fastq_uuid}?replica=aws" > ${right_fastq_name}
    echo "Unzipping"
    gunzip ${left_fastq_name}
    gunzip ${right_fastq_name}
    echo "Getting first 10k lines from input files"
    left_fastq_base=$(basename ${left_fastq_name} .gz)
    right_fastq_base=$(basename ${right_fastq_name} .gz)
    head -n10000 ${dollar}{left_fastq_base} > left_10000.fastq
    head -n10000 ${dollar}{right_fastq_base} > right_10000.fastq
  >>>
  runtime {
    docker: "gcr.io/broad-dsde-mint-dev/aws"
    memory: "2 GB"
    disks: "local-disk 10 HDD"
  }
  output {
    File local_left_fastq = "left_10000.fastq"
    File local_right_fastq = "right_10000.fastq"
  }
}

task calc_expression {
  File left_fastq
  File right_fastq

  command {
    echo "Aligning fastqs and calculating expression"
    rsem-calculate-expression -p 1 --paired-end ${left_fastq} ${right_fastq} /data/hg19_ucsc_genomeStudio_genes/rsem_trans_index output
    cut -f 1,5 output.isoforms.results > output_matrix.txt
    echo "Created output.transcript.bam and output_matrix.txt"
    echo "Creating qc matrix"
    cp output_matrix.txt qc_matrix.txt
    echo "Wrote qc matrix"
  }
  runtime {
    docker: "gcr.io/broad-dsde-mint-dev/rsem"
    memory: "2 GB"
    disks: "local-disk 10 HDD"
  }
  output {
    File bam = "output.transcript.bam"
    File matrix = "output_matrix.txt"
    File qc_matrix = "qc_matrix.txt"
  }
}

task submit {
  File bam
  File matrix
  File qc_matrix
  File provenance_script

  command <<<
    echo "Creating provenance.json"
    python ${provenance_script} provenance.json
    echo "Wrote provenance.json"

    python <<CODE
    import requests
    
    headers = {
        'Content-Type': 'application/hal+json',
        'Accept': 'application/hal+json'
    }
    json = {
        'submitter' : { 'email' : 'green@test.org'},
        'team' : { 'name' : 'green'}
    }
    url = 'http://submission-dev.ebi.ac.uk/api/submissions'
    print('Starting submission')
    print('POST {0}'.format(url))
    response = requests.post(url, headers=headers, json=json)
    if response.status_code < 400:
      print('{0}'.format(response.status_code, response.json()))
    else:
        print(response.text)
        response.raise_for_status()
    CODE
  >>>
  runtime {
    docker: "gcr.io/broad-dsde-mint-dev/aws"
    memory: "2 GB"
  }
  output {
    File provenance_json = "provenance.json"
  }
}

workflow mock_smartseq2 {
  String bundle_uuid
  String bundle_version
  File provenance_script

  call get_inputs {
    input:
      bundle_uuid = bundle_uuid,
      bundle_version = bundle_version
  }

  call localize {
    input:
      left_fastq_uuid = get_inputs.inputs[0][0],
      left_fastq_name = get_inputs.inputs[0][1],
      right_fastq_uuid = get_inputs.inputs[1][0],
      right_fastq_name = get_inputs.inputs[1][1]
  }

  call calc_expression {
    input:
      left_fastq = localize.local_left_fastq,
      right_fastq = localize.local_right_fastq
  }

  call submit {
    input:
      bam = calc_expression.bam,
      matrix = calc_expression.matrix,
      qc_matrix = calc_expression.qc_matrix,
      provenance_script = provenance_script
  }
}
