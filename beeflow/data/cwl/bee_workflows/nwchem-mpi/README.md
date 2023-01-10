## NWChem MPI Workflow

This is a simple example MPI workflow that should run on x86 systems.  The
client script needs to first package up this directory:
`beeflow/data/cwl/bee_workflows/nwchem-mpi`.  Then you should be able to
submit the workflow to the WFM after packaging with the client as well. An
example submission is below with the `nwchem.cwl` and `nwchem.yml` files
specified.

```
Welcome to BEE Client! 🐝
0) Package Workflow
1) Submit Workflow
2) List Workflows
3) Start Workflow
4) Query Workflow
5) Pause Workflow
6) Resume Workflow
7) Cancel Workflow
8) Copy Workflow
9) ReExecute Workflow
10) Exit
$ 1
Workflow name:
$ nwchem-mpi-2
Workflow tarball path:
$ ./nwchem-mpi.tgz
Main cwl file:
$ nwchem.cwl
Does the job have a yaml file (y/n):
$ y
Yaml file:
$ nwchem.yml
Submitting
Job submitted! Your workflow id is d9a1482e-782e-4323-bb5e-aedfd77e0228.
```

At this point the job can then be started just as with any other workflow.

This workflow pulls the x86 container from DockerHub, so if the container is not
working for some reason, I've included an example Dockerfile that should build
with Charliecloud. See `beeflow/data/dockerfiles/Dockerfile.nwchem-x86_64`.
NWChem is a massive program, so the build may take upwards of an hour depending
on the system.
