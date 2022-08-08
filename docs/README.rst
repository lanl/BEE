# BEE Documentation
The doc directory contains BEE documentation.

The HTML BEE documentation is stored in the `doc/sphinx` directory.
Documentation is automatically generated using Sphinx. 

Building documentation in the poetry environment automatically gathers the version of beeflow. This may work in a python environtment with poetry installed also.

.. code-block::

    cd <path to BEE repo>
    poetry shell
    cd doc/sphinx
    make html

To view build in _build:

.. code-block::

    open _build/html/index.html 

