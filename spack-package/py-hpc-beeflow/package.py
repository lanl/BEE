# Copyright 2013-2022 Lawrence Livermore National Security, LLC and other
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
#     spack install py-hpc-beeflow
#
# You can edit this file again by typing:
#
#     spack edit py-hpc-beeflow
#
# See the Spack documentation for more information on packaging.
# ----------------------------------------------------------------------------

from spack import *
from spack.package import *


class PyHpcBeeflow(PythonPackage):
    """BEE is a workflow orchestration system designed to build 
    containerized HPC applications and orchestrate workflows 
    across HPC and cloud systems."""

    homepage = "https://lanl.github.io/BEE/"
    pypi     = "hpc-beeflow/hpc-beeflow-0.1.3.tar.gz"

    maintainers = ['pagrubel', 'aquan9', 'jtronge', 'rstyd']

    version('0.1.3', sha256='a16590868dda85ba950c4f15334c8e5b649a680ca910043ce74405f2fb1ae987')

    #Build system
    depends_on('py-poetry-core@1.0.0:', type='build')

    #Dependencies
    depends_on('py-pip', type=('build', 'run'))
    depends_on('gcc', type=('build','run'))
    depends_on('py-python-daemon', type=('build','run'))
    depends_on('py-flask', type=('build','run'))
    depends_on('py-markupsafe', type=('build','run'))
    depends_on('neo4j@4.0.0:', type=('build','run'))
    depends_on('charliecloud', type=('build','run'))
    depends_on('py-pyyaml', type=('build','run'))
    depends_on('py-flask-restful', type=('build','run'))
    depends_on('py-celery@4.4.7:', type=('build','run'))
    depends_on('py-redis', type=('build','run'))
    depends_on('py-pylint', type=('build','run'))
    depends_on('py-apscheduler', type=('build','run'))
    
    depends_on('py-cwl-utils', type=('build','run'))
    depends_on('py-jsonpickle', type=('build','run'))
    depends_on('py-requests-unixsocket', type=('build','run'))

    def patch(self):
        # See https://python-poetry.org/docs/pyproject/#poetry-and-pep-517
        with working_dir(self.build_directory):
            if self.spec.satisfies('@:0.1.3'):
                filter_file("poetry>=0.12", "poetry_core>=1.0.0", 'pyproject.toml')
                filter_file(
                    "poetry.masonry.api", "poetry.core.masonry.api", 'pyproject.toml'
                )
