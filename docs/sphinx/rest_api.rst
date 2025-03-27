BEEflow REST API
**************************

This is a REST API for beeflow itself. It provides a way to remotely submit workflows to the system. 
The REST API was created primarily for the purpose of connecting CI resources to beeflow, but could also be used to setup remote "workers". 

:module: beeflow.remote.remote
:show-refs: True


Usage
-----
The following sequence of commands can be used to remotely prepare and submit workflows to the system:

.. code-block::

    beeflow remote connection $SSH_TARGET # check the connection to the Beeflow client
    beeflow remote core-status $SSH_TARGET # Check the status of Beeflow and the components
    beeflow remote droppoint $SSH_TARGET # get the drop point location on the remote machine
    beeflow remote copy $USER $SSH_TARGET $PATH # copy path for the workflow to the droppoint
    beeflow remote submit $SSH_TARGET $WF_NAME $TARBALL $MAIN_CWL $YAML # submit the workflow

Example of preparing and remotely submitting the cat-grep-tar workflow:

.. code-block::

    beeflow remote droppoint $SSH_TARGET
    beeflow package $BEE_PATH/examples/cat-grep-tar .
    beeflow remote copy $USER $SSH_TARGET cat-grep-tar.tgz
    mkdir cat-grep-tar-workdir
    cp $BEE_PATH/examples/cat-grep-tar/lorem.txt cat-grep-tar-workdir
    beeflow remote copy $USER $SSH_TARGET cat-grep-tar-workdir
    beeflow remote submit $SSH_TARGET test_remote cat-grep-tar.tgz workflow.cwl input.yml


Endpoints
----------
.. autofunction:: beeflow.remote.remote.get_wf_status

.. autofunction:: beeflow.remote.remote.get_drop_point

.. autofunction:: beeflow.remote.remote.get_owner

.. autofunction:: beeflow.remote.remote.submit_new_wf

.. autofunction:: beeflow.remote.remote.submit_new_wf_long

.. autofunction:: beeflow.remote.remote.show_drops

.. autofunction:: beeflow.remote.remote.cleanup_wf_directory

.. autofunction:: beeflow.remote.remote.get_core_status
