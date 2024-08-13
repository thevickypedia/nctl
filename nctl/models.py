import multiprocessing
import pathlib
import socket

from pydantic import BaseModel, FilePath, PositiveInt
from pydantic_settings import BaseSettings


class Concurrency(BaseModel):
    """BaseModel to load the multiprocessing object reference.

    >>> Concurrency

    """

    cloudfront_process: multiprocessing.Process | None = None

    class Config:
        """Config to allow arbitrary types."""

        arbitrary_types_allowed = True


class EnvConfig(BaseSettings):
    """Configuration settings for environment variables.

    >>> EnvConfig

    """

    port: PositiveInt
    host: str = socket.gethostbyname("localhost") or "0.0.0.0"
    aws_profile_name: str | None = None
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_default_region: str | None = None
    ngrok_auth: str | None = None
    ngrok_config: FilePath | None = None
    distribution_id: str | None = None
    distribution_config: FilePath | None = None
    debug: bool = False

    @classmethod
    def from_env_file(cls, env_file: pathlib.Path) -> "EnvConfig":
        """Create Settings instance from environment file.

        Args:
            env_file: Name of the env file.

        Returns:
            EnvConfig:
            Loads the ``EnvConfig`` model.
        """
        return cls(_env_file=env_file)

    class Config:
        """Extra configuration for EnvConfig object."""

        extra = "ignore"
        hide_input_in_errors = True


concurrency = Concurrency()
env: EnvConfig | None = None
