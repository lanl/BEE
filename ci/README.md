# CI code

This directory contains all the scripts that are needed for configuring and
running BEE on a CI machine. `BATCH_SCHEDULER` is set in the environment by the
workflow to either `Slurm` or `Flux`, which is then used in various places in
these scripts. The scripts are as follows:

* `env.sh`: CI environment set up
* `batch_scheduler.sh`: Install and set up a batch scheduler
* `bee_install.sh`: Install BEE and python dependencies
* `bee_config.sh`: Generate the bee.conf
* `deps_install.sh`: Install external dependencies needed by BEE and batch schedulers
* `flux_install.sh`: Install flux and dependencies
* `inner_integration_test.sh`: Inner script for integration testing and running
   with specific batch scheduler
* `integration_test.py`: The actual integration test script; can be run locally
* `integration_test.sh`: Outer script for integration testing called from the
   github workflow
* `slurm_start.sh`: Start the Slurm batch scheduler
* `unit_tests.sh`: Run the unit tests

Note: The only script that you should be able to run locally without problems is
`integration_test.py`. The rest are designed for the CI environment and will
likely not work on a local machine.

## Integration tests

The integration tests are written as a Python script `integration_test.py`.
This test can be run locally after you've started BEE with `beeflow`, by just
launching the script `./ci/integration_test.py`.
