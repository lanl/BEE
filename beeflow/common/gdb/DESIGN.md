# Graph Database Design

## Basics

A Neo4j graph consists of nodes and relationships. Nodes can have labels (e.g. `:Label`) and properties (name value pairs like `name = "Pat"`). Relationships have a type (e.g. `:DEPENDS_ON`) and properties. Property values can be `number`, `string`, `boolean`, spatial (only `Point`), temporal (e.g. `Time`, `Date`, `Duration`), or composite types of the previous types (e.g. lists and maps).

## BEE Workflow Graph Entities

A BEE workflow is a DAG (currently implemented in Neo4j) that represents a workflow originally specified in a CWL (Common Workflow Language) file. The fundamental structure of the workflow is based on `Task` nodes and `DEPENDS_ON` relationships. There are other nodes and relationships that are used to represent other properties of the workflow such as `Metadata`, `Requirements`, `Hints`, `Inputs`, `Outputs`,  etc. BEE's nodes, relationships, and properties are documented below.

## List of Node Types
* Listed edges are **outgoing**. Nodes are english cased, edges are all caps.

### `:BEE`
* This is the head node to the Graph Database. All `:Workflow` nodes point to this head. Only one such node exists in the graph database.
* `name`: Is always named "Head"

### `:Workflow`
* Node representing a workflow
* `id`: unique ID for a workflow in this database
* `name`: name of workflow as a string
* `state`: state of entire workflow
    - See `states,py` for more information
* `:WORKFLOW_OF`: Edge between from `:Workflow` to `:BEE` node to denote workflows of a BEE instance

### `:Task`
* Node representing a single task in a workflow
* `id`: unique ID for every task in workflow
* `workflow_id`: `id` of the workflow the task belongs to
* `name`: name of task as a string
* `base_command`: command (and parameters) to be executed
* `stdout`: command output location for task
* `stdin`: error output location for task
* `:BEGINS`: Edge from `:Task` to `:Workflow` node to indicate using an input parameter from the workflow
* `:DEPENDS_ON`: Edge from a `:Task`(1) to a `:Task`(2). (2) must be completed before (1) can be submitted to the task manager. `:DEPENDS_ON` relationships are deduced by parsing CWL.

### `:Input`
* Node that contains information for an input either to a workflow or task
* `id`: Moniker for input
* `type` Type of input (e.g File, string)
* `value` Value of input
* `:INPUT_OF`: Edge from `:Input` to either `:Task` or `:Workflow` node to indicate being an input to the workflow or task
#### IF `:Input` node is `:INPUT_OF` a `:Task` node:
* `position`: Serial number for multiple inputs
* `source`: 

### `:Output`
* Node that contains information for an output either from a workflow or task
* `id`: Moniker for output
* `type` Type of output (e.g File, string)
* `value` Value of output
* `:OUTPUT_OF`: Edge from `:Output` to either `:Task` or `:Workflow` node to indicate being an output of the task or workflow.
#### If `:Output` node is `:OUTPUT_OF` a `:Workflow` node:
* `source`:
#### IF `:Output` node is `:OUTPUT_OF` a `:Task` node:
* `glob`: 

### `:Hint`
* Node specifying hints (optional parameters) for a task or workflow
* `params`: Array of hint parameters for workflow or task
* `:HINT_OF`: Edge from `:Hint` to either `:Task` or `:Workflow` node to indicate being a hint of task or workflow

### `:Requirement`
* Node specifying requirements (mandatory parameters) for a task or workflow
* `params`: Array of requirement parameters for workflow or task
* `:REQUIREMENT_OF`: Edge from `:Requirement` to either`:Task` or `:Workflow` node to indicate being a requirement of task or workflow

### `Metadata`
* Contains state of task in workflow
* `state`: State of the task being described (defaults to `WAITING`)
* :DESCRIBES`: edge to the `:Task` node whose metadata is being described



