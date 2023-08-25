import boto3
from botocore.exceptions import ClientError
import os
from typing import Optional


REGION_NAME: Optional[str] = os.getenv("AWS_REGION", default=None)
SECRETS_ENABLED: bool = os.getenv("SECRETS_ENABLED", default="false").strip().lower() == "true"
SECRETS_PATH: Optional[str] = os.getenv("SECRETS_PATH", default=None)

_ALL_SECRETS = None
_client = None


def _create_session():
    global _client
    if _client:
        return _client
    try:
        session = boto3.session.Session()
        _client = session.client(
            service_name='secretsmanager',
            region_name=REGION_NAME)
        return _client
    except ClientError as e:
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e


def _initialise_if_needed():
    try:
        if SECRETS_ENABLED:
            global _ALL_SECRETS
            if _ALL_SECRETS is None:
                _ALL_SECRETS = _get_all_secrets(
                    client=_create_session(),
                    secrets_path=SECRETS_PATH
                )
    except ClientError as e:
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e


def _get_all_secrets(client, secrets_path):
    return client.get_secret_value(SecretId=secrets_path)


def get_secret_or_env(key, default=None, value=None):
    if SECRETS_ENABLED:
        _initialise_if_needed()
        value = _ALL_SECRETS.get(key)
    return value if value is not None else os.environ.get(key, default=default)


if __name__ == '__main__':
    print(get_secret_or_env('GE_API_KEY'))
