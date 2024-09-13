"""Tab completion code for client terminal input."""
import readline
import contextlib


@contextlib.contextmanager
def filepath_completion():
    """Tab complete files and pathnames within a context."""
    old_delims = readline.get_completer_delims()
    readline.set_completer_delims(' \n\t')
    readline.parse_and_bind('tab: complete')
    try:
        yield
    finally:
        # Reset the completer
        readline.set_completer_delims(old_delims)
        readline.parse_and_bind('')
