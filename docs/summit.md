### To run on summit:

```
#### Create a new bee.conf for first time use

bee_cfg new

You need to know the path of the Charliecloud image that has depdencies for
beeflow.
Summit uses the LSF workload scheduler so when queried for that answer LSF.

### Fix user config file for summit
In  ~/.config/beeflow/bee.conf (or wherever your configuration file is)
you must change <account> to your account and set the time limit to an appropriate time.

