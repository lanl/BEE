import logging
import sys

class BeeFormatter(logging.Formatter):
    """Format a string for the log file.
    
    This is a place to apply rich text formatting.
    
    Level Values are:
    DEBUG: 10
    INFO: 20
    WARNING: 30
    ERROR: 40
    CRITICAL:50
    """

    # Log Colors
    BOLD_CYAN = "[01;36m"
    RESET = "[0m"
    BOLD_YELLOW = "[01;33m"
    BOLD_RED = "[01;31m"

    log_format = {
        "DEBUG": f"{BOLD_CYAN}%(levelname)s: %(msg)s {RESET}",
        "STEP_INFO": "%(msg)s",
        "INFO": "%(msg)s",
        "WARNING": f"{BOLD_YELLOW}%(levelname)s: %(msg)s{RESET}",
        "ERROR": f"{BOLD_RED}%(levelname)s: %(msg)s{RESET}",
        "CRITICAL": f"{BOLD_RED}%(levelname)s: %(msg)s{RESET}",
    }

    log_format_no_colors = {
        "DEBUG": "%(levelname)s: %(msg)s ",
        "STEP_INFO": "%(msg)s",
        "INFO": "%(msg)s",
        "WARNING": "%(levelname)s: %(msg)s",
        "ERROR": "%(levelname)s: %(msg)s",
        "CRITICAL": "%(levelname)s: %(msg)s",
    }


    def __init__(self, colors=True):
        self.log_fmt = self.log_format if colors else self.log_format_no_colors

    def format(self, record):
        """
        Args:
          record(logging.LogRecord): The part of the log record from which
                                        the information is to be extracted.
        Returns:
          str: String containing meaningful information from logs.
        """
        fmt = self.log_fmt[logging.getLevelName(record.levelno)]
        if sys.version_info[0] < 3:
            self._fmt = fmt
        else:
            self._style._fmt = fmt
        result = f"{msg_prefix}{logging.Formatter.format(self, record)}"
        return result

