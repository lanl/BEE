# Dockerfiles

This is a home for Dockerfiles which have been used during the execution of workflows by the BEE development team.

## VASP Build Requirements

The VASP Dockerfile requires the following files to build successfully:
- VASP 5.4.4 source code (`vasp.5.4.4.tar.gz`)
- VASP configurable Makefile (`makefile.include`)
- ScaLAPACK 1.0.3 installer (`scalapack_installer.tgz`)
- `symbol.inc-5.4.4.patch`
- BEE Application SSH Keys
  - `keys/config`
  - `keys/id_rsa`
  - `keys/id_rsa.pub`

Dockerfile.clamr-ffmpeg works on Chicoma a LANL resource on the turquoise network (ffmpeg is built in the container)
