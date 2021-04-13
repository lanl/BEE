## CWL `ScatterFeatureRequirement` Examples

Note about `infiles`.
Note about deleting files.
Note `InlineJavascriptRequirement`

In CWL, scattering is used to run a step on every element of a list of inputs.

### `scatter-strings.cwl`

This example runs a single step workflow. The workflow accepts a single input,
`deck_array`, and runs the `crank` step on each element of that array. The
`crank` step simply `echo`s the element to standard output. This example doesn't
represent any real workflow--it's a precursor to `scatter-files.cwl`. The
contents of `deck_array` are specified in `scatter-strings-job.cwl`:
```yaml
deck_array: [file1,file2]
```

Validate and run the code using `cwltool`:
```sh
$ cwltool --validate scatter-strings.cwl
$ cwltool scatter-strings.cwl scatter-strings-job.yml
```

This example doesn't produce any output, but you can verify that it ran multiple
steps by examing the output of `cwltool`:
```
INFO /Users/bhagwan/BEE/BEE_Private/.venv/bin/cwltool 3.0.20201203173111
INFO Resolved 'scatter-strings.cwl' to 'file:///Users/bhagwan/BEE/BEE_Private/examples/cwl/features/scatter/scatter-strings.cwl'
INFO [workflow ] start
INFO [workflow ] starting step crank
INFO [step crank] start
INFO [job crank] /private/tmp/docker_tmp7rajrwkl$ echo \
    file1
file1
INFO [job crank] completed success
INFO [step crank] start
INFO [job crank_2] /private/tmp/docker_tmpzsasl7o8$ echo \
    file2
file2
INFO [job crank_2] completed success
INFO [step crank] completed success
INFO [workflow ] completed success
{}
INFO Final process status is success
```

`PATH=$PATH:$PWD` is required to find the Python code. Remember to delete the
output directory (though it is excluded from the repository using the local
`.gitignore` file):
```sh
$ rm -rf outdir
```

### `scatter-files.cwl`

This example runs a single step workflow. The workflow accepts a single input, `file_array`, and runs the `crank` step on each element of that array. The `crank` step simply `cat`s the content of the scattered file it's running on. In a real workflow, `file_array` might be a list of input decks representing inputs to a parameter study series. The contents of `file_array` are specified in `scatter-files-job.cwl`:
```yaml
file_array: [
  {class: File, path: "infiles/file1"},
  {class: File, path: "infiles/file2"}
]
```
where `outdir: string` is the name of the directory to be created (from the
workflow's input). The `glob` line captures that directory as the step's output
(`inputs` is workflow input).

Validate and run the code using `cwltool`:
```sh
$ cwltool --validate scatter-files.cwl
$ cwltool scatter-files.cwl scatter-files-job.cwl
```

This example doesn't produce any output, but you can verify that it ran multiple steps by examing the output of `cwltool`.
```
INFO /Users/bhagwan/BEE/BEE_Private/.venv/bin/cwltool 3.0.20201203173111
INFO Resolved 'scatter-files.cwl' to 'file:///Users/bhagwan/BEE/BEE_Private/examples/cwl/features/scatter/scatter-files.cwl'
INFO [workflow ] start
INFO [workflow ] starting step crank
INFO [step crank] start
INFO [job crank] /private/tmp/docker_tmp__9o8sb3$ cat \
    /private/tmp/docker_tmp90qlbn6x/stgb76f3026-b2e8-48a8-ae07-b6d4cd1ff27b/file1
This is infiles/file1.
INFO [job crank] completed success
INFO [step crank] start
INFO [job crank_2] /private/tmp/docker_tmpshizy5xu$ cat \
    /private/tmp/docker_tmpudds91ua/stg3324d128-9307-42a9-a841-a26aa7e18687/file2
This is infiles/file2.
INFO [job crank_2] completed success
INFO [step crank] completed success
INFO [workflow ] completed success
{}
INFO Final process status is success
```

### `scatter-dir.cwl`

This example runs a two-step workflow. The workflow accepts a single input,
`deck_dir`, which contains the files to be scattered over:
```yaml
deck_dir: {class: Directory, path: "infiles"}
```
The `infiles` directory and its contents are part of this repository.

The `collect_decks` step gathers the contents of this directory into an array,
`decks`, that is then scattered over by the following `crank` step. Note that we
use JavaScript to retrieve the contents of the directory, via the
`InlineJavascriptRequirement`. As far as I can tell, this step is necessary in
CWL. If you wish to avoid JavaScript, you could run a shell script, prior to
workflow execution, that would read the contents of the directory and make a
workflow input file similar to `scatter-files-job.cwl` (above). 
The relavant CWL code is:
```yaml
steps:
  collect_decks:
    run:
      class: ExpressionTool
      requirements: { InlineJavascriptRequirement: {} }
      inputs:
        dir: Directory
      expression: '${return {"decks": inputs.dir.listing};}'
      outputs:
        decks: File[]
    in:
      dir: deck_dir
    out: [decks]
```

Validate and run the code using `cwltool`:
```sh
$ cwltool --validate scatter-dir.cwl
$ cwltool scatter-dir.cwl scatter-dir-job.cwl
```

This example doesn't produce any output, but you can verify that it ran multiple steps by examing the output of `cwltool`.
```
INFO /Users/bhagwan/BEE/BEE_Private/.venv/bin/cwltool 3.0.20201203173111
INFO Resolved 'scatter-dir.cwl' to 'file:///Users/bhagwan/BEE/BEE_Private/examples/cwl/features/scatter/scatter-dir.cwl'
INFO [workflow ] start
INFO [workflow ] starting step collect_decks
INFO [step collect_decks] start
INFO [step collect_decks] completed success
INFO [workflow ] starting step crank
INFO [step crank] start
INFO [job crank] /private/tmp/docker_tmp4yjk109m$ cat \
    /private/tmp/docker_tmpqxc2h819/stgd81f94b7-dade-4920-955c-7f10ad58f426/file2
This is infiles/file2.
INFO [job crank] completed success
INFO [step crank] start
INFO [job crank_2] /private/tmp/docker_tmp07ls5p9s$ cat \
    /private/tmp/docker_tmpgwaqzyzk/stgf14a01d5-283c-4250-a9a5-6a0b54af6627/file1
This is infiles/file1.
INFO [job crank_2] completed success
INFO [step crank] completed success
INFO [workflow ] completed success
{}
INFO Final process status is success
```

### `scatter-dot.cwl`

This example runs a single-step workflow that scatters over _two_ input arrays:
`deck_array` and `dir_array`:
```yaml
deck_array: [file1,file2]
dir_array: [dir1, dir2]
```
If using the `dotproduct` scatter method, the arrays must be of equal length and
the scatter step will be run once for each pair of inputs (e.g.
[file1,dir1],...). If either of the `..._crossproduct` methods are used the
arrays may be of different lengths and the step will be run as a cartesian
product of the two arrays (e.g. `[file1,dir1]`, `[file1, dir2]`,...). The
relavant CWL is:
```yaml
    scatter: [deck, dir]
    scatterMethod: dotproduct
    # also try nested_crossproduct and flat_crossproduct
    in:
      deck: deck_array
      dir: dir_array
    out: []
```

Validate and run the code using `cwltool`:
```sh
$ cwltool --validate scatter-dot.cwl
$ cwltool scatter-dir.cwl scatter-dot-job.cwl
```

This example doesn't produce any output, but you can verify that it ran multiple
steps by examing the output of `cwltool`.
```
INFO /Users/bhagwan/BEE/BEE_Private/.venv/bin/cwltool 3.0.20201203173111
INFO Resolved 'scatter-dot.cwl' to 'file:///Users/bhagwan/BEE/BEE_Private/examples/cwl/features/scatter/scatter-dot.cwl'
INFO [workflow ] start
INFO [workflow ] starting step crank
INFO [step crank] start
INFO [job crank] /private/tmp/docker_tmp3hz91p_f$ echo \
    file1 \
    dir1
file1 dir1
INFO [job crank] completed success
INFO [step crank] start
INFO [job crank_2] /private/tmp/docker_tmpl8vj09fd$ echo \
    file2 \
    dir2
file2 dir2
INFO [job crank_2] completed success
INFO [step crank] completed success
INFO [workflow ] completed success
{}
INFO Final process status is success
```
