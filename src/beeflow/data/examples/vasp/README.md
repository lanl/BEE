**Note**: If this is difficult to read, use your browser's *Zoom In* (&#8984;+) 
and *Zoom Out* (&#8984;-) feature to change the text size.

## Building a VASP Workflow

This repository contains files, codes, and scripts to create binary, Docker,
and Charliecloud versions of VASP and execute them as part of a representative
workflows. Multiple workflow languages (e.g. BEE, CWL) and engines (e.g. BEE,
Toil) are usd to specify and execute the workflows.

VASP will demonstrate a second prototype workflow for the BEE project (as a
2019 deliverable). As a side benefit of this work, we will determine the
correct way to build VASP on various platforms (including binary, Docker, and
Charliecloud) to benefit the users at LANL--whether they're running on
Docker/Cc or not.

```sh
docker build --build-arg http_proxy="http://proxyout.lanl.gov:8080" \
             --build-arg https_proxy="https://proxyout.lanl.gov:8080" \
             . -t losalamosal/ch-vasp
```

### VASP at LANL

VASP is an atomic-scale materials modeling code use extensively at Los
Alamos. An important restriction to keep in mind is that VASP is **not** open
source. VASP's licensing model comes down to this: if you publish results based
on running the VASP code, you'd better have a license. Licenses appear to be
granted to an institution, such as LANL, with a *gatekeeper* appointed to
control distribution of the VASP software within the institution (ping me and
I'll let you know who LANL's gatekeeper is). If you want to use the code in
this repository you'll first need to contact the gatekeeper to get a copy of
the software (currently instantiated via two tarballs).

> **WARNING** Since VASP isn't open source, you must **NOT** post the source
> code to any external (non-LANL) sites. I don't believe that VASP is export
> controlled, so access by LANL foreign nationals is allowed. So, make use of
> `.gitignore` to prevent the upload of VASP tarballs to Git repositories.

### VASP Resources

The resources in this list were useful when creating the VASP build
process. Future VASP releases may invalidate some (or all) of these resorces.

* [Installing VASP](https://cms.mpi.univie.ac.at/wiki/index.php/Installing_VASP):
  seems to be the main source of information for building VASP. Mentions VASP all
  the way up to 5.4.4 (which is the version we're using here) and appears to
  provide accurate information.
* [Spack project 5 page](https://github.com/spack/spack/projects/5) documents
  issues with Spack and Charliecloud.
* [Spack CoMD](https://github.com/spack/spack/blob/4ecb465a366de3f722aeb1525b22c0d22aefceae/var/spack/repos/builtin/packages/comd/package.py):
  `package.py` file for CoMD application. An example of *Spackifying* an
  application (as we intend to do with VASP).
* [VASP Forums](https://cms.mpi.univie.ac.at/vasp-forum/forum.php): in
  particular, the installation forum.

### Building VASP

The build process for VASP is not very well documented. It seems that periodic
releases of VASP require updates to makefiles that are not well specified. This
section describes how to compile the **current** version (5.4.4) of VASP:

- [Manually](#building-vasp-manually): Download dependencies, or use
  pre-insatlled ones, edit the makefile and compile with resident compilers.
- [Spack Build](#using-spack-to-build-vasp-on-darwin): Use Spack to fully
  automate the build for various platforms and compilers.
- [Docker](#building-a-vasp-docker-container): Use Docker inside of a virtual
  machine to create a Docker container for VASP. The Docker container can then
  be fed to Charliecloud for execution.

#### Obtain VASP source

As mentioned above, contact LANL's gatekeeper to obtain the current VASP
source. Currently, two tarballs (`vasp.5.4.4.tar.gz` and `vasp.5.lib.tar.gz`)
contain the VASP source. If you get different types, numbers, or names of files
from the gatekeeper, the code in this repository may not work (as previously
mentioned, new releases of VASP sometimes break the build process/model).

This repo's `.gitignore` file is aggressive in excluding any `.tar` file to
prevent accidental upload of the source to any Git repositories.

#### VASP dependencies

Regardless of how VASP (the parallel version) is built, the following are
required dependencies:

* FORTRAN and C compilers.
* An MPI implementation. VASP folklore says that version 2.1.0 (or greater) is
  required. We hope that this does not conflict with Charliecloud (which also
  requires a specific version of OpenMPI).
* Numerical libraries:
  * BLAS
  * LAPACK
  * ScaLAPACK
  * FFTW


#### Building VASP manually

Trying to build VASP manually helps us work our way through finding and
compiling dependencies, determining compiler vendors and versions, selecting
compatible versions of OpenMPI, and making changes to the makefiles. This
knowledge is useful for getting a baseline version of VASP running
and feeding the construction of Spack configuration files.

##### Building VASP manually on __Darwin__

Before getting started, if at LANL, make sure you have your proxies configured:

```bash
export HTTP_PROXY=http://proxyout.lanl.gov:8080
export HTTPS_PROXY=http://proxyout.lanl.gov:8080
export http_proxy=$HTTP_PROXY
export https_proxy=$HTTPS_PROXY
export NO_PROXY=lanl.gov
```

Decide where you want to build VASP. Typically, a good place is in the root of
this cloned repository:

```bash
> git clone https://gitlab.lanl.gov/BEE/vasp.git
> cd vasp
> export VASP_HOME=$PWD
```

Get the VASP tarballs from LANL's gatekeeper and untar them. Note that the
installation site (above) states that the VASP library now resides at
`VASP_HOME/src/lib` and the the `vasp.5.lib.tar.gz` file is not used any
more.

```bash
> cd $VASP_HOME
> tar xzf vasp.5.4.4.tar.gz
```

Most of VASP's dependencies (compilers, OpenMPI, FFTW) are available as modules
on __Darwin__. We only need to download and install ScaLAPACK.

> **NOTE**: My (Al's) experience indicates that the easiest way to build VASP
> is to use the GNU compilers and download ScaLAPACK for most numerical
> dependencies. Attempting to use the Linux package managers to install BLAS,
> LAPACK, etc. proved to be a bit problematic. ScaLAPACK includes all numerical
> dependencies (except for FFTW3) and removes the need for additional (possibly
> incompatible) installs.

```bash
> module load gcc          # gcc/6.4.0(default)
> module load fftw/3.3.4
> module load openmpi/2.1.2-gcc_6.4.0
```

ScaLAPACK can be obtained
from [Netlib](http://www.netlib.org/scalapack/). There is also
a [README](http://netlib.org/scalapack/scalapack_installer/README) that
describes the installation process. To install ScaLAPACK (and any missing
libraries such as BLAS or LAPACK):

```bash
> wget http://www.netlib.org/scalapack/scalapack_installer.tgz
> tar xzf scalapack_installer.tgz
> cd scalapack_installer
> export SCALAPACK_HOME=$PWD
> ./setup.py --downall
> # ... build process takes a while...
```

With the modules loaded (GCC, FFTW, and OpenMPI) and ScaLAPACK, LAPACK, and
BLAS installed, you now have all required dependencies for VASP:

- BLAS: `$SCALAPACK_HOME/install/lib -lrefblas` (shown at end of ScaLAPACK build)
- LAPACK: `$SCALAPACK_HOME/install/lib -ltmg -lreflapack` (shown at end of ScaLAPACK build)
- BLACS/ScaLAPACK: `$SCALAPACK_HOME/install/lib -lscalapack` (shown at end of ScaLAPACK build)
- FFTW: `/projects/opt/centos7/fftw/3.3.4` (from `module display fftw/3.3.4`)

You now need to modify the VASP default makefile to to point to local
dependencies. First, copy the makefile template for Linux and Gnu compilers
(with MPI):

```bash
> cd $VASP_HOME/cd vasp.5.4.4
> cp makefile.include.linux_gnu makefile.include
```

Edit `makefile.include` and make the following changes:

From
```makefile
LIBDIR     = /opt/gfortran/libs/
LAPACK     = -L$(LIBDIR) -ltmglib -llapack
FFTW       ?= /opt/gfortran/fftw-3.3.4-GCC-5.4.1
```
to
```makefile
SCALAPACK_HOME = # yours...
LIBDIR     = $(SCALAPACK_HOME)/install/lib
LAPACK     = -L$(LIBDIR) -ltmg -lreflapack
FFTW       ?= /projects/opt/centos7/fftw/3.3.4
```

Finally, per
the
[VASP intall instructions](https://cms.mpi.univie.ac.at/wiki/index.php/Installing_VASP) we
need to make a couple of changes because we're using a version of LAPACK >= 3.6
(3.8 as of this writing).

Add `CPP_OPTIONS += -DLAPACK36` near the top of the `makefile.include`
file. Add the following lines to the end of
`$VASP_HOME/vasp.5.4.4/src/symbol.inc`:

```gfortran
! routines replaced in LAPACK >=3.6 
#ifdef LAPACK36
#define DGEGV DGGEV
#endif
```

You're ready to compile VASP:

```bash
> cd $VASP_HOME/vasp.5.4.4
> make std gam ncl
```

After successful compilation, try a couple of test runs. First, get a 2-node
allocation on __Darwin__ and then run the test across those nodes.

```bash
> salloc -N 2 -p galton  # this will place you on one of the nodes (e.g. cn30)
> cd $VASP_HOME/TestCu
> mpirun -mca btl ^openib $VASP_HOME/vasp.5.4.4/bin/vasp_std
> grep Elap OUTCAR   # to see execution time
> cd $VASP_HOME/TestTi
> mpirun -mca btl ^openib $VASP_HOME/vasp.5.4.4/bin/vasp_std
> grep Elap OUTCAR   # to see execution time
> # for both tests ignore IEEE_UNDERFLOW_FLAG IEEE_DENORMAL warnings
```

#### Using Spack to Build VASP on __Darwin__

[Spack](https://spack.io/) is an HPC-focused package manager designed to
simplify the process of building and maintaining HPC applications for multiple
platforms, compilers, libraries, etc. This sections explains how to build a
single configuration of VASP, on __Darwin__, using Spack. I'm not convinced
that it's a useful exercise--Spack is complicated and has a steep learning
curve. However, if this Spack process can be expanded to support multiple
compilers (e.g.Gnu, Intel) and platforms (e.g x86, Power) it may get prove
useful for the wider VASP-using community at Los Alamos.


Before getting started, if at LANL, make sure you have your proxies configured:

```bash
export HTTP_PROXY=http://proxyout.lanl.gov:8080
export HTTPS_PROXY=http://proxyout.lanl.gov:8080
export http_proxy=$HTTP_PROXY
export https_proxy=$HTTPS_PROXY
export NO_PROXY=lanl.gov
```

Now, choose a location and install Spack by cloning its repository and
initializing your shell environment:

```sh
> git clone https://github.com/spack/spack.git
> cd spack
> export SPACK_ROOT=$PWD
> . $SPACK_ROOT/share/spack/setup-env.sh    # if not using Bash or Zsh see Spack docs
```

The previous two lines should be executed at each login, so you may as well
place them in your `.zshrc` or `.bashrc`. Once these have been executed, you do
not need to be in the Spack repository to work with it. So, move back to the
root directory of this repository:

```sh
> cd $VASP_HOME
```

We want our __Darwin__ build of VASP, using Spack, to start as close to the
manual build as possible. After all, we know that build works. So, we need to
configure Spack to recognize and use the versions of the Gnu compilers (6.4.0)
and the OpenMPI library (2.1.3) that we used for the manual build. We'll
install everything else (FFTW, BLAS, LAPACK, ScaLAPACK) using Spack.

The following will show you the compilers that Spack currently recognizes. The
one shown was picked up by Spack from our path.

```sh
> spack compilers
==> Available compilers
-- gcc centos7-x86_64 -------------------------------------------
gcc@4.8.5
```

We need to edit Spack's `compilers.yaml` file to add the 6.4.0 version of the
Gnu compilers on __Darwin__ (accessed via the `module` command).

```sh
> spack config edit compilers
```

It should look something like:

```yaml
compilers:
- compiler:
    environment: {}
    extra_rpaths: []
    flags: {}
    modules: []
    operating_system: centos7
    paths:
      cc: /usr/bin/gcc
      cxx: /usr/bin/g++
      f77: /usr/bin/gfortran
      fc: /usr/bin/gfortran
    spec: gcc@4.8.5
   target: x86_64
```

You need to add the additional compiler (at the end of the file):

```yaml
compilers:
- compiler:
    environment: {}
    extra_rpaths: []
    flags: {}
    modules: []
    operating_system: centos7
    paths:
      cc: /usr/bin/gcc
      cxx: /usr/bin/g++
      f77: /usr/bin/gfortran
      fc: /usr/bin/gfortran
    spec: gcc@4.8.5
   target: x86_64
- compiler:
   environment: {}
   extra_rpaths: []
   flags: {}
   modules: [gcc/6.4.0]
   operating_system: centos7
   paths:
     cc: /projects/opt/centos7/gcc/6.4.0/bin/gcc
     cxx: /projects/opt/centos7/gcc/6.4.0/bin/g++
     f77: /projects/opt/centos7/gcc/6.4.0/bin/gfortran
     fc: /projects/opt/centos7/gcc/6.4.0/bin/gfortran
   spec: gcc@6.4.0
   target: x86_64
```

Note two things about this addition: `modules: [gcc/6.4.0]` is the module name
on __Darwin__, and `/projects/opt/centos/...` which come from running the
`module show gcc/6.4.0` command.

Now you should see the following:

```sh
> spack compilers
-- gcc centos7-x86_64 -------------------------------------------
gcc@6.4.0  gcc@4.8.5
```

Now we need to do something similar to recognize the desired version of the
OpenMPI library:

```sh
> spack config edit packages
```

The initial file will be empty and we need to add the following code to the
file:

```yaml
packages:
  openmpi:
    modules:
      openmpi@2.1.3%gcc@6.4.0 arch=linux-centos7-x86_64: openmpi/2.1.3-gcc_6.4.0
    buildable: False
```

You can see that Spack recognizes it:

```sh
> spack spec openmpi
Input spec
--------------------------------
openmpi

Concretized
--------------------------------
==> Warning: Could not detect module function ...      # ignore these
openmpi@2.1.3%gcc@6.4.0~cuda+cxx_exceptions fabrics=verbs ...   # long line
```

Now we begin the process of creating a Spack *package* for VASP. First, we need
to make the VASP source available to Spack. Most of the time, source will be
provided by a public GitHub repository. However, since VASP is licensed and
__not open source__ we need to use a local file as the source:

```bash
> cd $VASP_HOME
> ls
vasp.5.4.4.tar.gz
> pwd
/home/bhagwan/BEE/vasp
```

Using the above path and file name, the local VASP source URL will be:

```bash
file:///home/bhagwan/BEE/vasp/vasp.5.4.4.tar.gz
```

Now, figure out what the URL is for your account and file location.

We will now add a *package* for VASP to Spack's repository (we'll __never push__ it up
to the public repo though!):

```bash
> spack create file:///home/bhagwan/BEE/vasp/vasp.5.4.4.tar.gz  # use YOUR URL
# Answer 1 to the checksum question
```

This will create a package directory for VASP and open up an editor with a
default package file loaded. Clip the two lines:

```YAML
url      = "file:///your_url..."
    
version('5.4.4', sha256='your checksum...')
```

and save them somewhere. Exit the editor (with save) to keep the default file.

Now we'll replace the default package file with the one in this repository
(safe since you've copied the important lines). We also copy over a patch file
that's needed to update the VASP source for LAPACK versions greater than 3.6:

```bash
> cp package.py $SPACK_ROOT/var/spack/repos/builtin/packages/vasp
> cp symbol.inc-5.4.4.patch $SPACK_ROOT/var/spack/repos/builtin/packages/vasp
```

Now we need to edit the the `package.py` file that you just copied and paste in
your specific URL and checksum:

```bash
> spack edit vasp
```

Remove the two lines:

```yaml
url      = "file:///home/bhagwan/BEE/vasp/vasp.5.4.4.tar.gz"
    
version('5.4.4', sha256='5bd2449462386f01e575f9adf629c08cb03a13142806ffb6a71309ca4431cfb3')
```

and replace them with the ones you copied out of the default file. Exit your
editor (with save) to write the new file. You're now ready to build VASP. It's
important to have as close to a *clean environment* as you can. So, make sure
that the Gnu compiler and OpenMPI modules are **not** loaded. Spack knows where
they are based on the edits we performed on the `compilers.yaml` and
`packages.yaml` files.

```bash
> spack install vasp %gcc@6.4.0 ^openmpi@2.1.3
```

You can verify successful installation using `spack find`:

```bash
> spack find -p vasp
==> 1 installed package
-- linux-centos7-x86_64 / gcc@6.4.0 -----------------------------
    vasp@5.4.4  /home/bhagwan/spack/opt/spack/linux-centos7-x86_64/gcc-6.4.0/vasp-5.4.4-pz2cl5vok3m4pkkdfwl7psrsi55wuqak
> spack cd -i vasp
> ls -l bin
total 41344
-rwxr-xr-x 1 bhagwan bhagwan 10309512 Mar 22 15:05 vasp_gam
-rwxr-xr-x 1 bhagwan bhagwan 10461304 Mar 22 15:05 vasp_ncl
-rwxr-xr-x 1 bhagwan bhagwan 10428384 Mar 22 15:05 vasp_std
```

#### Building a VASP Docker Container


