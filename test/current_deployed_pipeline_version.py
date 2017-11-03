#!/usr/bin/env python
"""
Parses the TSV file {mint_deployment_dir}/{env}.tsv and returns
the version from the first line in the column named {pipeline_name}.
For example, given the following TSV:
10x	ss2
1.0.0	2.0.0
0.9.3	1.2.3

If pipeline_name is 10x, returns "1.0.0".
If pipeline_name is ss2, returns "2.0.0".

"""

import argparse
import csv

def run(pipeline_name, mint_deployment_dir, env):
    with open('{0}/{1}.tsv'.format(mint_deployment_dir, env)) as f:
        reader = csv.DictReader(f, delimiter='\t')
        row = reader.next()
        print(row[pipeline_name])

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--pipeline_name', required=True)
    parser.add_argument('--mint_deployment_dir', required=True)
    parser.add_argument('--env', required=True)
    args = parser.parse_args()
    run(args.pipeline_name, args.mint_deployment_dir, args.env)
