import yaml
import logging
import socket

from pydantic import PositiveInt, FilePath
from pydantic_settings import BaseSettings
from src.logger import LOGGER


def create_ngrok_config(token: str, filename: str):
    config = {
        'version': "2",
        'authtoken': token
    }
    with open(filename, 'w') as file:
        yaml.dump(stream=file, data=config, Dumper=yaml.Dumper, default_flow_style=False)


class EnvConfig(BaseSettings):
    port: PositiveInt
    host: str = socket.gethostbyname('localhost') or "0.0.0.0"
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_default_region: str | None = None
    ngrok_auth: str | None = None
    ngrok_config: FilePath | None = None
    distribution_id: str | None = None
    distribution_config: FilePath | None = None
    debug: bool = False

    class Config:
        env_file = ".env"
        extra = "ignore"


env = EnvConfig()

if env.debug:
    LOGGER.setLevel(logging.DEBUG)
else:
    LOGGER.setLevel(logging.INFO)

if env.ngrok_config:
    LOGGER.info("Using ngrok config file: %s", env.ngrok_config)
elif env.ngrok_auth:
    filename = "ngrok.yml"
    LOGGER.info("Creating ngrok config file as %s", filename)
    create_ngrok_config(env.ngrok_auth, filename)
    env.ngrok_config = filename

assert any((env.distribution_id, env.distribution_config)), \
    "Any one of 'distribution_id' or 'distribution_config' is required"
