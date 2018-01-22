#!/usr/bin/env python

"""
Green box description FIXME: elaborate
"""
import os
import json
import logging
import connexion
from connexion.resolver import RestyResolver
import argparse

import config

parser = argparse.ArgumentParser()
parser.add_argument('--host', default='0.0.0.0')
parser.add_argument('--port', type=int, default=8080)
args, _ = parser.parse_known_args()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('Lira | {module_path}'.format(module_path=__name__))

app = connexion.App(__name__)

# 'application' is not used in this file, but is used by gunicorn
application = app.app

config_path = os.environ['listener_config']
with open(config_path) as f:
    app.app.config = config.ListenerConfig(json.load(f), app.app.config)

resolver = RestyResolver('lira.api', collection_endpoint_name='list')
app.add_api('lira.yml', resolver=resolver, validate_responses=True)

if __name__ == '__main__':
    app.run(host=args.host, port=args.port)
