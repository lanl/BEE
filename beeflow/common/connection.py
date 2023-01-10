"""Connection class for connecting to other components over a socket."""
import urllib
import os
import requests

import requests_unixsocket


class Connection:
    """Connection for sending/receiving requests from a component."""

    def __init__(self, socket, prefix=None, error_handler=None):
        """Construct a new connection from a socket path."""
        self._socket_path = urllib.parse.quote(socket, safe='')
        self._session = requests_unixsocket.Session()
        self._prefix = prefix
        self._error_handler = (error_handler if error_handler is not None
                               else lambda resp: resp)

    def _full_url(self, path):
        """Get the full url for a path."""
        # For some reason urllib.parse.urljoin() is just returning `path` here
        # return urllib.parse.urljoin('http+unix://{self._socket_path}', path)
        if self._prefix is not None:
            path = os.path.join(self._prefix, path)
        return os.path.join(f'http+unix://{self._socket_path}', path)

    def handle_error(self, resp):
        """Handle an error, if there is one."""
        if resp.status_code != requests.codes.okay:  # noqa (pylama can't find the okay member)
            return self._error_handler(resp)
        return resp

    def get(self, path, *pargs, **kwargs):
        """Do an HTTP GET request."""
        return self.handle_error(self._session.get(self._full_url(path),
                                                   *pargs, **kwargs))

    def put(self, path, *pargs, **kwargs):
        """Do an HTTP PUT request."""
        return self.handle_error(self._session.put(self._full_url(path),
                                                   *pargs, **kwargs))

    def post(self, path, *pargs, **kwargs):
        """Do an HTTP POST request."""
        return self.handle_error(self._session.post(self._full_url(path),
                                                    *pargs, **kwargs))

    def delete(self, path, *pargs, **kwargs):
        """Do an HTTP DELETE request."""
        return self.handle_error(self._session.delete(self._full_url(path),
                                                      *pargs, **kwargs))

    def patch(self, path, *pargs, **kwargs):
        """Do an HTTP PATCH request."""
        return self.handle_error(self._session.patch(self._full_url(path),
                                                     *pargs, **kwargs))
