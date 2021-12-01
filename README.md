# BEE: Build and Execute Environment
The goal of BEE (Build and Execution Environment) is to create a unified
software stack to _containerize_ HPC applications. A container is a package of
code (usually binaries) and all of that code's dependencies (libraries,
etc.). Once built, this container can be run on many different platforms. The
execution environment on each platform will download and install (for this
application only) all of the applications and dependencies into an isolated
user environment and then execute the code. Containers provide many benefits:

- Users can choose their own software stack (libraries, compilers, etc.) and
not be bound by the currently installed environment on any one machine.
- Codes can be run portably across numerous platforms--all dependencies will be
downloaded and installed at run time.
- Entire _workflow_ environments can be built into one or more containers. A user
can include visualization and analysis tools along with the application. They
will all work together as the application runs.
- Provenance and history can be tracked by storing containers in a historical
repository. At any time, an older container can be rerun (all of its
dependencies are stored with it). Execution is repeatable and interactions
between software components can be tracked.
- Functional testing can be performed on smaller, dissimilar machines--there is
no real need to test on the actual HPC platform (performance testing obviously
requires target hardware).

The BEE project uses Docker to containerize applications. Docker has become the de
facto standard container system and is used widely in cloud and web
environments. Continuous integration services have been built on Docker, allowing application
developers to describe compile and execution environments with Docker. When code is checked into 
a repository, it can be automatically tested across a suite of different software environments.

The BEE project supports launching applications using the [Charliecloud](https://github.com/hpc/charliecloud) HPC container runtime.  These applications can be executed on a traditional HPC cluster or an OpenStack cloud cluster.

# Running on Darwin

We use a custom Slurm built for the BEE project on Darwin, built against the Darwin admin maintained configs in `/etc/slurm/`. In order to use the Slurm rest interface on Darwin, you must set up and use this custom Slurm build:

```
export MODULEPATH=$MODULEPATH:/projects/beedev/modulefiles
module load slurmrestd
```

Then proceed as usual.

# Contributing

The BEE project adheres to style guidelines specified in `./setup.cfg`. Before attempting to commit and push changes, please install our pre-commit githooks by running the following command in project root:
If using `git --version` >= 2.9
```
git config core.hooksPath .githooks
```
Otherwise
```
cp .githooks/* .git/hooks/
```
Using these git hooks will ensure your contributions adhere to style guidelines required for contribution. You will need to repeat these steps for every `BEE_Private` repo you clone.

# Mail List and Contact

For bugs and problems report, suggestions and other general questions regarding the BEE project, Please subscribe to [BEE-LANL](https://groups.google.com/forum/#!forum/BEE-User-Group) and post your questions. 


# Release

This software has been approved for open source release and has been assigned **BEE C17056**.


# Publications

- [BeeFlow: A Workflow Management System for In Situ Processing across HPC and Cloud Systems, ICDCS, 2018](https://ieeexplore.ieee.org/abstract/document/8416366/)
- [Build and execution environment (BEE): an encapsulated environment enabling HPC applications running everywhere, IEEE BigData, 2018](https://ieeexplore.ieee.org/document/8622572)
- BeeSwarm: Enabling Parallel Scaling Performance Measurement in Continuous Integration for HPC Applications, ASE, 2021
- BEE Orchestrator: Running Complex Scientific Workflows on Multiple Systems, HiPC, 2021


# Copyright
License can be found [here](https://github.com/lanl/BEE/blob/master/LICENSE)
