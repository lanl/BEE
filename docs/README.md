# BEE Documentation
The HTML BEE documentation is stored in the `<path to BEE repo>/doc/sphinx` directory.
Documentation is automatically generated using Sphinx. 

For users with pip in their environment(may need to install hpc-beeflow, sphinx and sphinx-rtd-theme using pip):

```
    cd <path to BEE repo>/docs/sphinx
    make clean
    make html
```

For developers with a poetry environment and beeflow installed:

```
    cd <path to BEE repo>
    poetry shell
    cd docs/sphinx
    make html
```

To view:
```
    open _build/html/index.html
```



