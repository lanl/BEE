# Launching BEE on Dora/OpenStack

## Configuration

Most of the configuration for the cloud launcher script will be under the `[cloud]` section in the bee.conf. Here are the required parameters. These are not necessarily unique to Dora, but can also apply to GCE and other clouds if supported in the future.

* `private_key_file`: path to the private key file used for the head instance
* `bee_user`: user to be created on head instance (most likely the default user
   created -- cloud-user for RHEL and debian for debian images)
* `tm_listen_port`: listening port of the remote TM
* `wfm_listen_port`: listening port of the local WFM
* `head_node`: name of the head node where the TM will be launched
* `template_file`: path to the template file to launch the cloud setup from
* `provider`: name of provider (`google`, `openstack`, `chameleoncloud`)

As an example here is the current configuration that I'm using on my account:

```
[cloud]
private_key_file = /home/jtronge/key
bee_user = debian
tm_listen_port = 7777
tm_launch_cmd = /bee/tm
head_node = bee-server
template_file = /home/jtronge/BEE_Private/templates/dora-template.yaml
provider = openstack
```

Some of these parameters are redundant and can probably be removed in future iterations.

### Provider Specific Configuration

In order to launch stacks with different templates and providers, there is an extra section which corresponding to a given provider. These are names `[cloud.{provider}]` where provider is the provider name in lowercase. The contents of the section vary depending on the provider class and the template being used.

For the `templates/dora-template.yaml` here are the required parameters:

* `stack_name`:
* `key_name`:
* `public_next`: 
* `github_pat`:
* `git_branch`:
* `https_proxy`:
* `http_proxy`:
* `no_proxy`:
* `wfm_listen_port`:
* `tm_listen_port`:

## Launch Script

...

## Connecting

...

## Running BEE

To launch the workflow manager manually you'll need to make sure that
`$no_proxy` includes localhost, since this is how the WFM contacts the TM.

no_proxy=localhost,$no_proxy python -m beeflow.wf_manager ~/.config/beeflow/bee.conf

To launch a workflow you can run
`./src/beeflow/client/client_cli.py --workflow-path [PATH TO WORKFLOW]`, or use
the original client.py script.
