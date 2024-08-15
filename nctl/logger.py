import json
import logging

import yaml
from pydantic import BaseModel

LOGGER = logging.getLogger("nctl.tunnel")


class AddProcessName(logging.Filter):
    """Wrapper that overrides ``logging.Filter`` to add ``processName`` to the existing log format.

    >>> AddProcessName

    Args:
        process_name: Takes name of the process to be added as argument.
    """

    def __init__(self, process_name: str):
        """Instantiates super class."""
        self.process_name = process_name
        super().__init__()

    def filter(self, record: logging.LogRecord) -> bool:
        """Overrides the built-in filter record."""
        record.processName = self.process_name
        return True


class LogConfig(BaseModel):
    """BaseModel object for log configurations.

    >>> LogConfig

    """

    debug: bool = False
    process: str | None = None
    log_config: dict | str | None = None

    class Config:
        """Extra configuration for LogConfig object."""

        extra = "ignore"


def configure_logging(**kwargs) -> None:
    """Configure logging based on the parameters.

    Keyword Args:
        debug: Boolean flag to enable/disable debug mode.
        process: Name of the process to add a process name filter to default logging.
        log_config: Custom logging configuration.
    """
    config = LogConfig(**kwargs)
    if not config.process:
        config.process = "ngrok-cloudfront"
    if config.log_config:
        if isinstance(config.log_config, dict):
            logging.config.dictConfig(config.log_config)
        elif isinstance(config.log_config, str) and config.log_config.endswith(".json"):
            with open(config.log_config) as file:
                loaded_config = json.load(file)
                logging.config.dictConfig(loaded_config)
        elif isinstance(config.log_config, str) and config.log_config.endswith(
            (".yaml", ".yml")
        ):
            with open(config.log_config) as file:
                loaded_config = yaml.safe_load(file)
                logging.config.dictConfig(loaded_config)
        else:
            # See the note about fileConfig() here:
            # https://docs.python.org/3/library/logging.config.html#configuration-file-format
            logging.config.fileConfig(config.log_config, disable_existing_loggers=False)
    else:
        if config.debug:
            log_level = logging.DEBUG
        else:
            log_level = logging.INFO
        logging.getLogger(f"nctl.{config.process}").setLevel(log_level)
        default_formatter = logging.Formatter(
            datefmt="%b-%d-%Y %I:%M:%S %p",
            fmt="%(asctime)s - %(levelname)s - [%(module)s:%(processName)s:%(lineno)d] - %(funcName)s - %(message)s",
        )
        handler = logging.StreamHandler()
        handler.setFormatter(default_formatter)
        logging.getLogger(f"nctl.{config.process}").addHandler(handler)
        logging.getLogger(f"nctl.{config.process}").addFilter(
            filter=AddProcessName(process_name=config.process)
        )
