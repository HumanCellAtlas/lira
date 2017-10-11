#!/usr/bin/env python3
import os
import json
import logging
import connexion
from connexion.resolver import RestyResolver
from google.cloud import storage
from google.auth.exceptions import DefaultCredentialsError
from google.oauth2 import service_account
from .config import ListenerConfig
logging.basicConfig(level=logging.DEBUG)
"""
Green box description FIXME: elaborate
"""


if __name__ == '__main__':
    app.run(debug=True, port=8080)