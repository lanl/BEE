# BEE Cloud Launcher

## Command Line Options

* YAML-based configuration file
* `--setup-cloud` - set up the remote cloud based on the passed in template
* `--tm` - start the Task Manager and set up the SSH connection to it
* `--copy-files` - convenience option for copying files to the instance
* `--debug` - show the generated template without making any API calls (use
   with `--setup-cloud`)

## Template Generation

The cloud launcher script takes a `template_file` option with a path to a
Jinja2 template file. This template will be rendered using the parameters from
the YAML configuration document and then passed to the provider for cloud
configuration. The rendered set up code must install and set up BEE.

## Providers

### Google Provider

Using Google Compute Engine as the provider requires the environment variable
`GOOGLE_APPLICATION_CREDENTIALS` to be set to the location of a Google
application credentials JSON file. The template generated is a YAML file with
an instances parameter containing a list of instances to be created along with
their various options. Only instance creation is supported right now, meaning
that some resources may need to be reserved using Google's web interface or the
`gcloud` command line tool. Teardown is also not implemented.

### OpenStack

For OpenStack, you need to make sure that your environment is set up with the
required credentials. The template should produce a valid Heat template that
will be used to set up a stack. Teardown of the stack can be done with the
command line or the Horizon web interface.

### Chameleon Cloud

To set up clusters on Chameleon Cloud you currently will need to use a Heat
template with the web interface. After set up in the web interface is complete,
you should make sure that the YAML configuration file has all the right info.
Then the other options such as `--copy-files` and `--tm` should work.

## Main Configuration Options

* `wfm_listen_port`: listen port that will be used by the WFM on the local machine
* `tm_listen_port`: listen port to configure for the TM
* `private_key_file`: private key file used to connect with SSH
* `bee_user`: name of user to log in as on the head node
* `tm_launch_cmd`: command to launch on the remote instance to start the TM
* `head_node`: name or ID of the head node that is used to find the instance
   using the particular cloud's API
* `template_file`: path to a Jinja2 template file (see `dora.jinja2` for an
   example)
* `provider`: name of the provider (`google`, `chameleoncloud`, `openstack`)
