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
resolver = RestyResolver("green_box.api", collection_endpoint_name="list")
app.add_api('../green_box.yml', resolver=resolver, validate_responses=True)
