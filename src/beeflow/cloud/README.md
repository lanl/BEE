# BEE Cloud Code

## Command Line Options

* Bee configuration file
* `--setup` - set up the remote cloud
* `--install-tm` - install the Task Manager on the remote cloud head node
* `--tm` - start the Task Manager and set up the SSH connection to it

## CloudInfo File

TODO: Document cloud launcher configuation, options and set up.

* `head_node_ip_addr` -
* `bee_srcdir` -

## Providers

### Google Provider

Using Google Compute Engine as the provider requires the environment variable
`GOOGLE_APPLICATION_CREDENTIALS` to be set to the location of a Google
application credentials JSON file.

### Chameleon Cloud

To set up clusters on Chameleon Cloud you currently will need to use a Heat
template with the web interface. After set up in the web interface is complete,
you should make sure that the configuration file has all the right info and
also fill out the CloudInfo file to allow the Cloud Launcher to connect to the
cloud.

## Configuration Options

* cloud\_workdir - workdir used for cloud data
* provider - cloud provider
* node\_count - number of nodes to create
* ram\_per\_vcpu - RAM per each VCPU
* vcpu\_per\_node - number of VCPUs per node
* bee\_user - name of user on the remote nodes
* private\_key\_file - private key file to use (will be generated if it doesn't
  exist)
* storage - URL of workflow cloud storage
* bee\_code - BEE code tarball (this is needed right now since BEE is a private
  repository)
