Enhanced BEE Client Installation Instructions
---------------------------------------------

First install ``nvm`` from `here
<https://github.com/nvm-sh/nvm#installing-and-updating>`_. This is a node.js
package manager.

Next, you can install dependencies with ``npm install``. If you are running on a
VPN or you're traffic is directed through a proxy, you will need to temporarily
turn it off and unset the proxy environment variables (``http_proxy``,
``https_proxy``, ``HTTP_PROXY``, ``HTTPS_PROXY``).

Finally, start the app with ``npm start``. This can be done with the VPN and
proxy on, since all packages should already be installed.
