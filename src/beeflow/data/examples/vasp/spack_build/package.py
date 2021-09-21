# Copyright 2013-2019 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

# ----------------------------------------------------------------------------
# If you submit this package back to Spack as a pull request,
# please first remove this boilerplate and all FIXME comments.
#
# This is a template package file for Spack.  We've put "FIXME"
# next to all the things you'll want to change. Once you've handled
# them, you can save this file and test your package like this:
#
#     spack install vasp
#
# You can edit this file again by typing:
#
#     spack edit vasp
#
# See the Spack documentation for more information on packaging.
# ----------------------------------------------------------------------------

from spack import *


class Vasp(MakefilePackage):
    """VASP: Atomic scale materials modeling (LANL version)"""

    homepage = "https://cms.mpi.univie.ac.at/wiki/index.php/Installing_VASP"
    # Change these for your particular file location and checksum
    url      = "file:///Users/bhagwan/tmp/VASP/vasp/vasp.5.4.4.tar.gz"
    version('5.4.4', sha256='5bd2449462386f01e575f9adf629c08cb03a13142806ffb6a71309ca4431cfb3')

    # Parallel build of VASP fails--unable to locate FORTRAN modules!
    parallel = False

    # VASP depends on these. Should lock down required versions too.
    depends_on('fftw')
    depends_on('blas')
    depends_on('lapack')
    depends_on('scalapack')
    depends_on('mpi')

    # Patching src/symbol.inc per https://cms.mpi.univie.ac.at/wiki/index.php/Installing_VASP
    # Don't know why level=0 is needed here--should be default?
    patch('symbol.inc-5.4.4.patch', level=0)

    def edit(self, spec, prefix):
        # These edits are vaild for ONLY version 5.4.4 of VASP
        copy('arch/makefile.include.linux_gnu', 'makefile.include')
        makefile = FileFilter('makefile.include')

        makefile.filter('-Duse_shmem', '-Duse_shmem \\\n\t-DLAPACK36')

        makefile.filter('LIBDIR\s*= .*', '# LIBDIR = ')
        makefile.filter('BLAS\s*= .*', 'BLAS = -L%s -lblas' % self.spec['lapack'].prefix)
        makefile.filter('LAPACK\s*= .*', 'LAPACK = -L%s -llapack' % self.spec['lapack'].prefix)
        makefile.filter('SCALAPACK\s*= .*', 'SCALAPACK = -L%s -lscalapack' % self.spec['netlib-scalapack'].prefix)
        makefile.filter('/opt/gfortran/fftw-3.3.4-GCC-5.4.1', spec['fftw'].prefix)

    def install(self, spec, prefix):
	install_tree('bin', prefix.bin)
