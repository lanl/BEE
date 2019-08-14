 BEE Documentation Generation with Sphinx
The `doc-src` directory contains the source for generating BEE documentation.

BEE documentation is generated using [Sphinx](http://www.sphinx-doc.org/en/master/).
API documentation may be automatically generated using docstrings.

---

### Install Sphinx

Before generating documentation, make sure the `Sphinx` and `sphinx-rtd-theme` packages are installed.

If using Poetry, run the command `poetry install`.

Otherwise, run the command `pip install Sphinx sphinx-rtd-theme`.

---

### Generate the Documentation

To generate HTML documentation, simply run the command `make html` inside the `doc-src` directory.
The generated documentation is stored in the untracked `doc-src/_build/html` directory.

Sphinx is also capable of generating documentation in other formats, such as LaTeX (`latex`, or `latexpdf` for PDF),
JSON (`json`), Pickle (`pickle`), plain text (`text`), and manual pages (`man`).
For a full list of documentation types, run the command `make` in the project root directory.

---

### Adding Documentation

To create a new index for the table of contents, create a reST file with an appropriate name in the `doc-src` directory.

To add the new index to the table of contents, append the name of the index, without the `.rst` extension to the `toctree`
section of `index.rst`, indented with *precisely 3 spaces*. For example, if a file is created with the name `foo.rst`,
then `index.rst` should appear as:

```rst
.. toctree::
   :maxdepth: 2
   :caption: Contents:

   foo
```

---

### Autodoc Generation

Make sure that the up-to-date `beeflow` package has been built using `poetry build` or `poetry install` and is in your
Python path before generating documentation. If it is not, then uncomment the following lines in `conf.py`:

```py
# import os
# import sys
# sys.path.insert(0, os.path.abspath('./beeflow'))
```

**Warning**: currently, o generate documentation for a module that uses the `wf_interface` module, Neo4j must first be
running to avoid an exception from occurring while `sphinx-build` is running.

To automatically generate documentation for a Python module, create a section with the following format in a reST file:

```rst
Descriptive Module Name
=======================
.. automodule:: hierarchy.of.module
   :members:
```

For example:

```rst
Workflow Data Structures
========================
.. automodule:: beeflow.common.data.wf_interface
   :members:
```

- To document a specific class in a module, use the `autoclass` directive instead of the `automodule` directive.

- To document private members (those that begin with `_`), add the `:private-members:` option below `:members:`.

- To document special members (those that begin and end with `__`), add the `:special-members:` option below `:members:`.

---

### More Sphinx Information

For more information about using Sphinx, check out the following resources:

- https://www.sphinx-doc.org/en/1.5/tutorial.html
- https://buildmedia.readthedocs.org/media/pdf/brandons-sphinx-tutorial/latest/brandons-sphinx-tutorial.pdf
- https://docs.readthedocs.io/en/stable/intro/getting-started-with-sphinx.html
