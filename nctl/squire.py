import json
import logging
import os
import pathlib
import shutil

import yaml

from nctl import models

LOGGER = logging.getLogger("nctl.tunnel")


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


def envfile_loader(filename: str | os.PathLike) -> models.EnvConfig:
    """Loads environment variables based on filetypes.

    Args:
        filename: Filename from where env vars have to be loaded.

    Returns:
        EnvConfig:
        Returns a reference to the ``EnvConfig`` object.
    """
    env_file = pathlib.Path(filename)
    sfx = env_file.suffix.lower()
    if sfx == ".json":
        with open(env_file) as stream:
            env_data = json.load(stream)
        return models.EnvConfig(**{k.lower(): v for k, v in env_data.items()})
    if sfx in (".yaml", ".yml"):
        with open(env_file) as stream:
            env_data = yaml.load(stream, yaml.FullLoader)
        return models.EnvConfig(**{k.lower(): v for k, v in env_data.items()})
    if sfx in (".text", ".txt", ""):
        return models.EnvConfig.from_env_file(env_file)
    raise ValueError(
        "\n\tUnsupported format for 'env_file', can be one of (.json, .yaml, .yml, .txt, .text, or null)"
    )


def load_env(**kwargs) -> models.EnvConfig:
    """Merge env vars from env_file with kwargs, giving priority to kwargs.

    See Also:
        This function allows env vars to be loaded partially from .env files and partially through kwargs.

    Returns:
        EnvConfig:
        Returns a reference to the ``EnvConfig`` object.
    """
    if env_file := kwargs.get("env_file"):
        file_env = envfile_loader(env_file).model_dump()
    elif os.path.isfile(".env"):
        file_env = envfile_loader(".env").model_dump()
    else:
        file_env = {}
    merged_env = {**file_env, **kwargs}
    return models.EnvConfig(**merged_env)


def run_validations() -> None:
    """Validates the loaded environment variables and checks ngrok CLI availability.

    Raises:
        AssertionError:
        If any of the validations fail.
    """
    assert shutil.which(
        cmd="ngrok"
    ), "\n\tTo proceed, please install ngrok CLI using https://dashboard.ngrok.com/get-started/setup"
    assert any(
        (models.env.distribution_id, models.env.distribution_config)
    ), "\n\tAny one of 'distribution_id' or 'distribution_config' is required"
    if models.env.distribution_config:
        assert models.env.distribution_config.suffix.lower() in (
            ".yml",
            ".yaml",
            ".json",
        ), "\n\tConfig file can only be JSON or YAML"
    if models.env.ngrok_config:
        LOGGER.info("Using ngrok config file: %s", models.env.ngrok_config)
    elif models.env.ngrok_auth:
        config_file = "ngrok.yml"
        LOGGER.info("Creating ngrok config file as %s", config_file)
        create_ngrok_config(models.env.ngrok_auth, config_file)
        models.env.ngrok_config = config_file
