"""Path conversion code."""
import os


class PathError(Exception):
    """Path error class."""

    def __init__(self, *args):
        """Construct a path error object."""
        self.args = args


def _components(path):
    """Convert a path into a list of components."""
    if not os.path.isabs(path):
        raise PathError('Bind mounts and workdir paths must be absolute')
    path = os.path.normpath(path)
    return [comp for comp in path.split('/') if comp]


def convert_path(path, bind_mounts):
    """Convert a path outside the container to a path inside the container."""
    comps = _components(path)
    for outside, inside in bind_mounts.items():
        outside = _components(outside)
        inside = _components(inside)
        if comps[:len(outside)] == outside:
            base = comps[len(outside):]
            inside.extend(base)
            new_path = '/'.join(inside)
            return f'/{new_path}'
    return path
