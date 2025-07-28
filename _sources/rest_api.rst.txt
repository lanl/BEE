BEEflow REST API
**************************

This is a REST API for beeflow itself. It provides a way to remotely submit workflows to the system. 
The REST API was created primarily for the purpose of connecting CI resources to beeflow, but could also be used to setup remote "workers". 

:module: beeflow.remote.remote
:show-refs: True


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
