## Build and Execute Environment (BEE) User Guide for `Batch-Mode`

The following guide shows you how to use Batch-Mode on `BEE-VM`.

Batch mode allows you to run multiple nodes with each node running different scripts.

##### Step 1. Preparation
Follow the `Installation` section of `User Guide for BEE-VM` to install and setup BEE.

##### Step 2. Configure task file
* (1) Follow the related section of `User Guide for BEE-VM` to configure beefile.
* (2) Set `batch_mode` to be `true` to turn on batch mode.
* (3) In the `general_run`, fill in scripts information that will be run on different nodes.
* (4) Make sure the number of scripts matches the number of nodes (i.e. `node_list` for `BEE-VM`).

#### Step 3. Launch task
Run task same as launching regular `BEE-VM` task.
