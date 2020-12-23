import logging
import sys
import os

STEP_INFO = 15
logging.addLevelName(STEP_INFO, "STEP_INFO")


class LogFormatter(logging.Formatter):
    """Format a string for the log file.
    
    This is a place to apply rich text formatting.
    
    Level Values are:
    DEBUG: 10
    STEP_INFO: 15
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
        "STEP_INFO": "%(levelname)s: %(msg)s",
        "INFO": "%(levelname)s: %(msg)s",
        "WARNING": f"{BOLD_YELLOW}%(levelname)s: %(msg)s{RESET}",
        "ERROR": f"{BOLD_RED}%(levelname)s: %(msg)s{RESET}",
        "CRITICAL": f"{BOLD_RED}%(levelname)s: %(msg)s{RESET}",
    }

    log_format_no_colors = {
        "DEBUG": "%(levelname)s: %(msg)s ",
        "STEP_INFO": "%(levelname)s: %(msg)s",
        "INFO": "%(levelname)s: %(msg)s",
        "WARNING": "%(levelname)s: %(msg)s",
        "ERROR": "%(levelname)s: %(msg)s",
        "CRITICAL": "%(levelname)s: %(msg)s",
    }


    def __init__(self, colors):
        """Initialize formatted loggers.

        :param colors: Format with or without ANSI Escape Code color formatting
        :type colors: Bool
        """
        self.log_fmt = self.log_format if colors else self.log_format_no_colors

    def format(self, record):
        """Format record for logging.

        :param record: The part of the log record to extract info from.
        :type record: logging.LogRecord
        """
        fmt = self.log_fmt.get(logging.getLevelName(record.levelno))
        return logging.Formatter(fmt).format(record)

class BeeLogger(logging.Logger):
    """ Extend Python logger to handle custom log category."""

    def step_info(self, msg="", *args, **kwargs):
        """ Log a messagewith severity 'STEP_INFO'.

        :param msg: Message to be logged
        :type msg: String
        :param *args: List of non-key worded, variable length args.
        :type *args: list
        :param **kwargs: Key-worded, variable length args.
        :type **kwargs: dict
        """
        if self.isEnabledFor(STEP_INFO):
            self._log(STEP_INFO, msg, args, **kwargs)

class LevelFilter(logging.Filter):
    """Filters the level that are to be accepted and rejected."""

    def __init__(self, passlevels, reject):
        self.passlevels = passlevels
        self.reject = reject

    def filter(self, record):
        """Returns True and False according to the pass levels and reject value.

        :param record: Record from logs
        :type record: logging.LogRecord
        """
        if self.reject:
            return record.levelno not in self.passlevels
        else:
            return record.levelno in self.passlevels


def setup_logging(level="STEP_INFO", colors=True):
    """Setup logger.

    :param level: Level to be logged in logger.
    :type level: String
    """
    logging.setLoggerClass(BeeLogger)
    log = logging.getLogger("bee")
    if log.hasHandlers():
        log.setLevel(level)
        return log
    else:
        formatter = LogFormatter(colors=colors)
    
        # Intermediate step info goes to stdout
        h1 = logging.StreamHandler(sys.stdout)
        h1.addFilter(LevelFilter([logging.INFO, STEP_INFO], False))
        h1.setFormatter(formatter)
    
        # All stepinfo goes to stdout
        h2 = logging.StreamHandler(sys.stdout)
        h2.addFilter(LevelFilter([logging.INFO, STEP_INFO], True))
        h2.setFormatter(formatter)
    
        log.addHandler(h1)
        log.addHandler(h2)
        log.setLevel(level)
        return log

def save_log(log, logfile):
    """Set log formatter for handle and add handler to logger.

    :param log: The logger object
    :type log: Logging.logger
    :param logfile: Path for the logfile
    :type logfile: String
    """
    dir = os.path.dirname(logfile)
    if not os.path.exists(dir) and dir != "":
        os.makedirs(dir)
    handler = logging.FileHandler(logfile)
    formatter = LogFormatter(colors=False)

    # Set
    handler.setFormatter(formatter)
    log.addHandler(handler)
