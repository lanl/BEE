## DRAFT: Preliminary Design

### Basics

A Neo4j graph consists of nodes and relationships. Nodes can have labels (e.g. `:Label`) and properties (name value pairs like `name = "Pat"`). Relationships have a type (e.g. `:DEPENDS_ON`) and properties. Property values can be `number`, `string`, `boolean`, spatial (only `Point`), temporal (e.g. `Time`, `Date`, `Duration`), or composite types of the previous types (e.g. lists and maps).

### BEE Workflow Graph Entities

A BEE workflow is a DAG (currently implemented in Neo4j) that represents a workflow originally specified in a CWL (Common Workflow Language) file. The fundamental structure of the workflow is based on `Task` nodes and `DEPENDS_ON` relationships. There are other nodes and relationships that are used to represent other properties of the workflow such as `Metadata`, `Requirements`, `Hints`, `REQUIRES`, etc. BEE's nodes, relationships, and properties are documented below.

### `:Task`

* `task_id`: unique ID for every task in workflow
* `name`: name of task as a string
* `command`: command (and parameters) to be executed
* `inputs`: array of inputs to task
* `outputs`: array of outputs of task
* `state`: state of task during execution of workflow
    - Still designing, but may be one of:
        - `WAITING`: These tasks are in the database and are waiting for the tasks that they are dependent on to `COMPLETE`
        - `READY`: These tasks are ready to be executed (sent to the task manager). The tasks they depend on are `COMPLETE` so al their inputs are available.
        - `SUBMITTED`: These tasks have been sent to to the task manager but we don't know that they're actually `RUNNING` until we hear that from the task manager.
        - `SUBMIT_FAIL`: The task manager attempted to submit a job for this task but there was a failure.
        - `PENDING`: The task has been submitted and the ensuing job is pending execution on the machine, message via task manager.
        - `RUNNING`: The task is actively executing on the machine. The task manager told us that this is true.
        - `CANCELLED`: The task has stopped because it was told to by the user or other entity. The task is not `COMPLETE` and tasks that depend on it can not be run (we can't assume all of its outputs were successfully created). The task manager tells us that the task was `CANCELLED`.
        - `CRASHED`: An abnormal termination. In other respects it's the same as `CANCELLED`.
        - `ZOMBIE`: We may use this to indicate an unknown state after a system crash or loss of connection to the task manager or if during query loop the task manager gets an error when trying to query for it. Maybe.
        - `COMPLETE`: The task has successfully completed execution and all of its outputs have been produced. Its dependent tasks may now be set to `READY`.
* `:DEPENDS_ON`: relationship(s) to `:Task`s that must complete before this task can run
    - This relationship has no properties
* `:HAS_METADATA`: relationship to `:TaskMetadata` for this task
    - This relationship has no properties
* `:HAS_REQUIREMENTS`: relationship to `:TaskRequirements` (must have) for this task
    - This relationship has no properties
* `:HAS_HINTS`: relationship to `:TaskHints` (may have) for this task
    - This relationship has no properties

#### `:TaskMedatata`, `:Metadata`

`:TaskMetadata` is also labelled as `:Metadata`. This is so that we can easily search the database for all metadata nodes (e.g. `:TaskMetadata`, `:WorkflowMetadata`).

#### `:TaskRequirements`, `:Requirements`

`:TaskRequirements` is also labelled as `:Requirements`. This is so that we can easily search the database for all requirements nodes (e.g. `:TaskRequirements`, `:WorkflowRequirements`).

#### `:TaskHints`, `:Hints`

`:TaskHints` is also labelled as `:Hints`. This is so that we can easily search the database for all hint nodes (e.g. `:TaskHints`, `:WorkflowHints`).

### `:Workflow`

* `workflow_id`: unique ID for the **single** workflow in this database
* `name`: name of workflow as a string
* `inputs`: array of inputs to workflow
* `outputs`: array of outputs of workflow
* `state`: state of entire workflow
    - Still designing, but may be one of:
        - `WAITING`: The workflow has been loaded into the database and is waiting to be started.
        - `RUNNING`: The actively is actively executing on the machine.
        - `CANCELLED`: The task has stopped because it was told to by the user or other entity. Examine the tasks in the database to determine their individual status.
        - `CRASHED`: An abnormal termination. In other respects it's the same as `CANCELLED`.
        - `ZOMBIE`: We may use this to indicate an unknown state after a system crash or loss of connection to other parts of the system (client, task manager, etc.)
        - `COMPLETE`: The workflow has successfully completed execution and all of its outputs have been produced.
* `:HAS_METADATA`: relationship to `:WorkflowMetadata` for this workflow
    - This relationship has no properties
* `:HAS_REQUIREMENTS`: relationship to `:WorkflowRequirements` (must have) for this workflow
    - This relationship has no properties
* `:HAS_HINTS`: relationship to `:WorkflowHints` (may have) for this workflow
    - This relationship has no properties

#### `:WorkflowMedatata`, `:Metadata`

`:WorkflowMetadata` is also labelled as `:Metadata`. This is so that we can easily search the database for all metadata nodes (e.g. `:TaskMetadata`, `:WorkflowMetadata`).

#### `:WorkflowRequirements`, `:Requirements`

`:WorkflowRequirements` is also labelled as `:Requirements`. This is so that we can easily search the database for all requirements nodes (e.g. `:TaskRequirements`, `:WorkflowRequirements`).

#### `:WorkflowHints`, `:Hints`

`:WorkflowHints` is also labelled as `:Hints`. This is so that we can easily search the database for all hint nodes (e.g. `:TaskHints`, `:WorkflowHints`).

