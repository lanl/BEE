=========
chameleon
=========
Use Centos 7 cloud images as the baseline for build Chameleon disk images.
This element contains the common customizations across all Chameleon sites & clusters:

- Set up CentOS repositories to use the UTexas mirror
- Disable SELinux
- Set up RDO repository
- Set up EPEL repository
- Install our patched version of cloud-init
- Install base packages
- Install g5k-checks and dependencies
- Configure cloud-init
- Set up console autologin

For further details see the redhat-common README.
