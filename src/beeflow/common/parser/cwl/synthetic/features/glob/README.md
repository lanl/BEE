## CWL Globbing Examples

Note about `outfiles`.
Note about deleting files.
Note `InlineJavascriptRequirement`

In CWL, globbing is used to capture output of a step.

### `glob-dir.cwl`

This example runs a single step workflow. The workflow accepts two inputs: the
name of the output directory to create and the number of files to write to it.
The output of the workflow is a directory of files (globbing is used to capture
these files). The workflow runs a simple Python code, `n-files-dir.py`, that
creates the output directory and fills it with the requested number of files.
The relavant lines of CWL are:
```yaml
...
inputs:
  outdir: string
  num: int
  ...
      outputs:
        dir:
          type: Directory
          outputBinding:
            glob: $(inputs.outdir)
...
```
where `outdir: string` is the name of the directory to be created (from the
workflow's input). The `glob` line captures that directory as the step's output
(`inputs` is workflow input).

Validate and run the code using `cwltool`:
```sh
$ cwltool --validate glob-dir.cwl
$ PATH=$PATH:$PWD cwltool glob-dir.cwl --outdir outfiles --num 50
```

`PATH=$PATH:$PWD` is required to find the Python code. Remember to delete the
output directory (though it is excluded from the repository using the local
`.gitignore` file):
```sh
$ rm -rf outdir
```
