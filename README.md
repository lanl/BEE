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
- Checkpoint and restore operations can happen at a higher level, e.g., node level. The entire
computation, as it sits in memory, can be saved and restarted, obviating the need
for application level checkpoints.

The BEE project uses Docker to containerize applications. Docker has become the de
facto standard container system and is used widely in cloud and web
environments. Continuous integration services have been built on Docker, allowing application
developers to describe compile and execution environments with Docker. When code is checked into 
a repository, it can be automatically tested across a suite of different software environments.


# Build Instructions

To be added

# Mail List and Contact

For bugs and problems report, suggestions and other general questions regarding the BEE project, Please subscribe to [BEE-LANL](https://groups.google.com/forum/#!forum/BEE-User-Group) and post your quesitons. 


# Release

This software has been approved for open source release and has been assigned **BEE C17056**.


# Publications

- [BeeFlow: A Workflow Management System for In Situ Processing across HPC and Cloud Systems](https://ieeexplore.ieee.org/abstract/document/8416366/)


# Copyright
License can be found [here](https://github.com/lanl/BEE/blob/master/LICENSE)
