These dockerfiles enable one to build comd with pmix support to use on a system that
does not have slurm with pmix support such as the Darwin test bed at LANL.

You can build a container using charliecloud (vers 0.27 +)

```
ch-image build -f Dockerfile.debian . --force
ch-image build -f Dockerfile.openmpi-3.1.5 .
ch-image build -f Dockerfile.comd-x86_64-wpmix .

# List images 
ch-image list

# Tar resultant image
ch-convert -o tar comd-x86_64-wpmix /usr/projects/beedev/comd/comd-x86_64-wpmix.tar.gz
```
