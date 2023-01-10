# CI code

This directory contains all the scripts that are needed for configuring and
running BEE on a CI machine. The scripts here are as follows:

* `env.sh`: CI environment set up
* `bee_install.sh`: script for installing BEE
* `bee_start.sh`: start script for BEE
* `deps_install.sh`: BEE external dependency install script (this installs
                     distro libs, as well as slurm)
* `slurm_start.sh`: script for configuring and launching a single-machine slurm
                    set up
* `integration_test.sh`: external script for setting up the environment for the
                         integration test
* `integration_test.py`: actual Python integration testing code

Note: The only script that you should be able to run locally without problems is
`integration_test.py`. The rest are designed for the CI environment and will
likely not work on a local machine.

## Integration tests

The integrations tests are written as a Python script `integration_test.py`.
This test can be run locally after you've started BEE with `beeflow`, by just
launching the script `./ci/integration_test.py`.
