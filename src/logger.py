import logging
from multiprocessing import current_process


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


LOGGER = logging.getLogger(__name__)
DEFAULT_LOG_FORM = "%(asctime)s - %(levelname)s - [%(processName)s:%(module)s:%(lineno)d] - %(funcName)s - %(message)s"
DEFAULT_FORMATTER = logging.Formatter(
    datefmt="%b-%d-%Y %I:%M:%S %p", fmt=DEFAULT_LOG_FORM
)
HANDLER = logging.StreamHandler()
HANDLER.setFormatter(DEFAULT_FORMATTER)
LOGGER.addHandler(HANDLER)
# todo: Should be within a function for process name filter to work
LOGGER.addFilter(filter=AddProcessName(process_name=current_process().name))
