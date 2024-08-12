import socket

from pydantic import PositiveInt
from pydantic_settings import BaseSettings


class EnvConfig(BaseSettings):
    port: PositiveInt
    host: str = socket.gethostbyname('localhost') or "0.0.0.0"
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_default_region: str | None = None
    ngrok_auth: str | None = None
    distribution_id: str | None = None

    class Config:
        env_file = ".env"
        extra = "ignore"


env = EnvConfig()
