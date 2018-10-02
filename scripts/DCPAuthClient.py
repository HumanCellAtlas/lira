import time

import base64
import functools
import json
import jwt
import requests
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime


class DCPAuthClient(object):
    audience = "https://dev.data.humancellatlas.org/"
    dev_deployments = ('dev', 'integration', 'test', 'staging')

    def __init__(self, path_to_json_key, trusted_google_project):
        self.path_to_json_key = path_to_json_key
        self.trusted_google_project = trusted_google_project

        if not any(deployment in trusted_google_project for deployment in DCPAuthClient.dev_deployments):
            self.audience = "https://data.humancellatlas.org/"

        self.__token = None
        # TODO: check the liveness of the token and make it as singleton if applicable
        self.issue_time = None
        self.expire_time = None

    def get_auth_header(self):
        return {'Authorization': 'Bearer {}'.format(self.token)}

    @property
    def token(self):
        credentials = DCPAuthClient._from_json(self.path_to_json_key)
        tok = DCPAuthClient.get_service_jwt(service_credentials=credentials, audience=self.audience)
        self.verify_jwt(tok, audience=self.audience, trusted_google_project=self.trusted_google_project)
        return self.__token

    @staticmethod
    def _from_json(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)

    @staticmethod
    @functools.lru_cache(maxsize=32)
    def get_openid_config(openid_provider):
        res = requests.get("https://{}/.well-known/openid-configuration".format(openid_provider))
        res.raise_for_status()
        return res.json()

    @staticmethod
    def get_jwks_uri(openid_provider):
        if openid_provider.endswith("iam.gserviceaccount.com"):
            return "https://www.googleapis.com/service_accounts/v1/jwk/{}".format(openid_provider)
        else:
            return DCPAuthClient.get_openid_config(openid_provider)["jwks_uri"]

    @staticmethod
    @functools.lru_cache(maxsize=32)
    def get_public_keys(openid_provider):
        keys = requests.get(DCPAuthClient.get_jwks_uri(openid_provider)).json()["keys"]
        return {
            key["kid"]: rsa.RSAPublicNumbers(
                    e=int.from_bytes(base64.urlsafe_b64decode(key["e"] + "==="), byteorder="big"),
                    n=int.from_bytes(base64.urlsafe_b64decode(key["n"] + "==="), byteorder="big")
            ).public_key(backend=default_backend())
            for key in keys
        }

    @staticmethod
    def get_service_jwt(service_credentials, audience):
        iat = time.time()
        exp = iat + 3600
        payload = {'iss': service_credentials["client_email"],
                   'sub': service_credentials["client_email"],
                   'aud': audience,
                   'iat': iat,
                   'exp': exp,
                   'https://auth.data.humancellatlas.org/email': service_credentials["client_email"],
                   'https://auth.data.humancellatlas.org/group': 'hca',
                   'scope': ["openid", "email", "offline_access"]
                   }
        additional_headers = {'kid': service_credentials["private_key_id"]}
        signed_jwt = jwt.encode(payload, service_credentials["private_key"], headers=additional_headers,
                                algorithm='RS256').decode()
        return signed_jwt

    def verify_jwt(self, token, audience, trusted_google_project):
        assert token
        try:
            openid_provider = "humancellatlas.auth0.com"
            token_header = jwt.get_unverified_header(token)
            public_keys = DCPAuthClient.get_public_keys(openid_provider)
            tok = jwt.decode(token, key=public_keys[token_header["kid"]], audience=audience)
        except KeyError:
            unverified_token = jwt.decode(token, verify=False)
            issuer = unverified_token["iss"]
            assert issuer.endswith("@{}.iam.gserviceaccount.com".format(trusted_google_project))
            token_header = jwt.get_unverified_header(token)
            public_keys = DCPAuthClient.get_public_keys(issuer)
            tok = jwt.decode(token, key=public_keys[token_header["kid"]], audience=audience)
        self.__token = token
        self.issue_time = datetime.fromtimestamp(tok['iat']).strftime('%Y-%m-%d %H:%M:%S')
        self.expire_time = datetime.fromtimestamp(tok['exp']).strftime('%Y-%m-%d %H:%M:%S')
