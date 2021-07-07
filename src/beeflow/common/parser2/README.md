# Sample CWL Workflow Files and Parsing Codes

This repository contains some (simple) sample CWL workflow
files. Additionally, there is some Python code (`dump_cwl.py`), using
the auto-generated CWL parser (`parser_v1_0.py`) to explore the CWL
files and print the Python classes that brepresent the CWL file.

Also included is a sample CWL parser that also uses
`parser_v1_0.py`. The parser reads a CWL fle (**only** `grepcount.cwl`
for now), parses it into python objects, and loads the Neo4j databse
with a workflow using the BEE workflow interface.

## Install Dependency

> **NOTE:** You don't need to do this is you're in a BEE development
> environment. Just make sure to do a `poetry update`.

Please install the Python parsing code using Poetry (make sure you're in an
active virtual environment for BEE).

Another useful tool to install is `cwltool`. Using this you can
validate a CWL file via `cwltool --validate file.cwl`.

```sh
$ poetry add -D cwl-utils cwltool
```

## Read the Parser's Documentation

Start a Python shell, load the parsing library, and explore the code's
documentation:

```sh
$ python       # 3.6 or greater
>>> import cwl_utils.parser_v1_0 as cwl
>>> top = cwl.load_document("./grepcount/grep-and-count.cwl")
INFO:rdflib:RDFLib Version: 4.2.2
>>> help(cwl)
Help on module cwl_utils.parser_v1_0 in cwl_utils:

NAME
    cwl_utils.parser_v1_0

DESCRIPTION
    # This file was autogenerated using schema-salad-tool --codegen=python
    # The code itself is released under the Apache 2.0 license and the help text is
    # subject to the license of the original schema.
    #

CLASSES
    builtins.Exception(builtins.BaseException)
        ValidationException
    builtins.object
...
```

All the usual Python exploration tools are useful as well (e.g. `vars`, `dir`,
etc.).

## Using the CWL Parser


`parse_cwl.py` demonstrates the use of the parser. Run it as follows
(making sure you have an empty Neo4j databse running):


```sh
$ ./parse_cwl.py ./grepcount/gc.cwl

```

This will load the `gc.cwl` file into the Neo4j databse as a
workflow. Since the databse is now populated, subsequent reruns of the
parser will fail--named objects already exist in the database. If you
want to experment with multiple runs, make sure you empth the databse
between runs using the followg command in the Neo4j browser.

```sh
MATCH(n) WITH n LIMIT 10000 DETACH DELETE n
```

## References

- [`cwl-utils` repository](https://github.com/common-workflow-language/cwl-utils)
