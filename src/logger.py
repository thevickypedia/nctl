import importlib
import logging
from multiprocessing import current_process

pname = current_process().name
if pname == "MainProcess":
    pname = "ngrok-cloudfront"


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


def build_logger() -> logging.Logger:
    """Constructs a custom logger.

    Returns:
        logging.Logger:
        Returns a reference to the logger object.
    """
    importlib.reload(logging)
    logger = logging.getLogger(__name__)
    default_formatter = logging.Formatter(
        datefmt="%b-%d-%Y %I:%M:%S %p",
        fmt="%(asctime)s - %(levelname)s - [%(processName)s:%(module)s:%(lineno)d] - %(funcName)s - %(message)s",
    )
    handler = logging.StreamHandler()
    handler.setFormatter(default_formatter)
    logger.addHandler(handler)
    logger.addFilter(filter=AddProcessName(process_name=pname))
    logger.setLevel(logging.INFO)
    return logger
