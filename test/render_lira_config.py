#!/usr/bin/env python

import argparse
import json
import re

def run(args):
    with open(args.env_config_file) as f:
        env_config = json.load(f)
    with open(args.secrets_file) as f:
        secrets_config = json.load(f)

    with open(args.template_file) as f:
        s = f.read()

    params_dict = vars(args)
    params_dict.update(env_config)
    for k, v in params_dict.items():
        s = s.replace('{{{0}}}'.format(k), v)
    config = json.loads(s)
    config.update(secrets_config)
    print(json.dumps(config, indent=2, sort_keys=True))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--template_file')
    parser.add_argument('--env_config_file')
    parser.add_argument('--secrets_file')
    parser.add_argument('--pipeline_tools_version')
    parser.add_argument('--10x_version')
    parser.add_argument('--ss2_version')
    args = parser.parse_args()
    run(args)
