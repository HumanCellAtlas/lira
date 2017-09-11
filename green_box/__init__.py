#!/usr/bin/env python

"""
Green box description FIXME: elaborate
"""

import os, sys, json, time, logging
from datetime import datetime, timedelta

from flask import Flask, request, redirect, jsonify
import connexion
from connexion.resolver import RestyResolver

logging.basicConfig(level=logging.DEBUG)

app = connexion.App(__name__)
app.app.config['MAX_CONTENT_LENGTH'] = 10 * 1000

config_path = os.environ['listener_config']
with open(config_path) as f:
    config = json.load(f)
    for key in config:
        app.app.config[key] = config[key]

resolver = RestyResolver("green_box.api", collection_endpoint_name="list")
app.add_api('../green_box.yml', resolver=resolver, validate_responses=True)
