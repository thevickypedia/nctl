import json
import logging
import os
import pathlib

import yaml

from src import logger, models

LOGGER = logger.build_logger()


def create_ngrok_config(token: str, filename: str) -> None:
    """Creates a config file for ngrok.

    Args:
        token: Ngrok auth token.
        filename: Filename to dump the config.
    """
    config = {"version": "2", "authtoken": token}
    with open(filename, "w") as file:
        yaml.dump(
            stream=file, data=config, Dumper=yaml.Dumper, default_flow_style=False
        )


def env_loader(filename: str | os.PathLike) -> models.EnvConfig:
    """Loads environment variables based on filetypes.

    Args:
        filename: Filename from where env vars have to be loaded.

    Returns:
        EnvConfig:
        Returns a reference to the ``EnvConfig`` object.
    """
    env_file = pathlib.Path(filename)
    if env_file.suffix.lower() == ".json":
        with open(env_file) as stream:
            env_data = json.load(stream)
        return models.EnvConfig(**{k.lower(): v for k, v in env_data.items()})
    elif env_file.suffix.lower() in (".yaml", ".yml"):
        with open(env_file) as stream:
            env_data = yaml.load(stream, yaml.FullLoader)
        return models.EnvConfig(**{k.lower(): v for k, v in env_data.items()})
    elif not env_file.suffix or env_file.suffix.lower() in (
        ".text",
        ".txt",
        "",
    ):
        return models.EnvConfig.from_env_file(env_file)
    else:
        raise ValueError(
            "\n\tUnsupported format for 'env_file', can be one of (.json, .yaml, .yml, .txt, .text, or null)"
        )


def validate_env() -> None:
    """Validates the loaded environment variables."""
    if models.env.debug:
        LOGGER.setLevel(logging.DEBUG)
    else:
        LOGGER.setLevel(logging.INFO)

    if models.env.ngrok_config:
        LOGGER.info("Using ngrok config file: %s", models.env.ngrok_config)
    elif models.env.ngrok_auth:
        config_file = "ngrok.yml"
        LOGGER.info("Creating ngrok config file as %s", config_file)
        create_ngrok_config(models.env.ngrok_auth, config_file)
        models.env.ngrok_config = config_file

    assert any(
        (models.env.distribution_id, models.env.distribution_config)
    ), "\n\tAny one of 'distribution_id' or 'distribution_config' is required"
