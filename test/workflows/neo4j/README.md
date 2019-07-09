# Create, Export, and Import Sample Noe4j Workflow Databases

This repository contains some basic notes on how to use Neo4j as it relates to
the BEE project (our machines, our specific goals, etc.) for testing via sample
databses (workflows). Every workflow in BEE will be represented by a single
Neo4j database. These workflows (and databases) will eventually be created by
parsing a CWL file and dynamically building the database from it. Until then,
the project will require samples to test and develop with. That is the purpose
of this repository.

## Getting Started

Neo4j can be installed and run in multiple ways. In this repo we describe how
to use Neo4j with Docker. Once you have the database running, databases can be
created and populated either manually or programmatically:

- Manually with the Cypher language in the browser.
- Manually with the Cypher language in a shell.
- Programmatically with Cypher scripts in the shell.
- Programmatically with the Python interface to Neo4j.

We'll discuss each of these, but first we need to learn how to run Neo4j in a
Docker container.

### Running Neo4j with Docker

It's easy to experiment with Neo4j if you have access to a machine that can run
Docker. Do it the easy way, on your Mac, with Docker installed. Or, do it the
hard way, on Darwin with Al's Packer VM or a Vagrant box with Docker
provisioned.

```sh
> docker run \
    --publish=7474:7474 --publish=7687:7687 \
    --name neo4j \
    --volume=$HOME/path/to/data:/data \
    --volume=$HOME/path/to/scripts:/scripts \
    --volume=$HOME/path/to/dumps:/dumps \
    -it neo4j /bin/bash
bash-4.4$ 
```

The directory mapped to `/data` is where the database (data, config, etc.) will
live. As far as I can tell, Neo4j can only support a single database. The
`--name` flag specifies the name of the container. The `neo4j` at the end of
the command is the image name (which will be fetched from Docker Hub if not
already downloaded).

The `/scripts` directory will be used to store `cypher-shell` scripts and the
`/dumps` directory will store exported databases. We'll discuss these
activities later in this document.

At this point, Neo4j is not yet running, but from within this shell (in the
`neo4j` container we just started with `docker run`) you can start/stop the
database, execute the Cypher shell, and export/import databases:

```sh
bash-4.4$ neo4j start
Active database: graph.db
Directories in use:
  home:         /var/lib/neo4j
  config:       /var/lib/neo4j/conf
  logs:         /logs
  plugins:      /var/lib/neo4j/plugins
  import:       /var/lib/neo4j/import
  data:         /var/lib/neo4j/data
  certificates: /var/lib/neo4j/certificates
  run:          /var/lib/neo4j/run
Starting Neo4j.
Started neo4j (pid 294). It is available at http://0.0.0.0:7474/
There may be a short delay until the server is ready.
See /logs/neo4j.log for current status.
bash-4.4$ neo4j status
Neo4j is running at pid 294
bash-4.4$ neo4j stop
Stopping Neo4j.. stopped
bash-4.4$ neo4j restart
Started neo4j (pid 452). It is available at http://0.0.0.0:7474/
There may be a short delay until the server is ready.
See /logs/neo4j.log for current status.
```

In a local browser, go to `http://localhost:7474/browser/`. If you're starting
with a brand new database, you'll be asked to change the password for the admin
(`neo4j`) account after getting past the default password prompt (also
`neo4j`). The browser provides a nice interface for administering the database
(users, etc.) and experimentation. Interface panes accept textual commands that
interact with the database. 

The language used is called Cypher (the same language can be used from a shell
as described later). Results of Cypher commands are shown in the browser as
text or with a graphical representation.

### Pausing or Terminating Neo4j with Docker

If you run in the shell environment (as described above), you can start/stop
Neo4j using the `neo4j` command:

```sh
bash-4.4$ neo4j stop
bash-4.4$ neo4j restart
```

When you exit the shell, you still need to stop the Docker container (and
remove the process if you want to rerun). Docker won't let you start a
container with the same name:

```sh
bash-4.4$ exit
> docker stop neo4j
> docker rm neo4j
> docker run --publish=7474:7474 --publish=7687:7687 ...
```

The above will restart the container with the existing database that's stored
in the mapped directory (`/data`). If you want to start clean, remove that
directory:

```sh
bash-4.4$ exit
> docker stop neo4j
> docker rm neo4j
> rm -rf $HOME/path/to/data     # or whatever you called yours
> docker run --publish=7474:7474 --publish=7687:7687 --name neo4j --volume=$HOME/path/to/data:/data ...
```

## Interacting with the Database

The Cypher language is used to interact with the graph database (add/delete
nodes and relationships, search, etc.). You can experiment with Cypher using
panes in the browser window. If you need to do more than experiment, it's
probably best to use Cypher (and Cypher scripts) from the command line or to
interact programmatically using Python.

> If you use the browser panes to enter Cypher commands you should enable
> "multi-statement query editor" in the _Settings_ panel. Then, if you have a
> single line command, you execute it with a RETURN key. If you have a
> multi-line command, make sure to hit SHIFT-RETURN at the end of the first
> command line. Subsequent lines can be entered with RETURNS. When you're ready
> to submit the entire command, hit CTRL-RETURN.
>
> This isn't an issue in `cypher-shell` as all commands must end with a
> semicolon. RETURN will just extend the command to a new line until you hit
> ;-RETURN.


### Using Cypher from the Command Line

From withing the shell in the `neo4j` Docker container, you can run
`cypher-shell` to access Cypher:

```sh
bash-4.4$ neo4j start
bash-4.4$ cypher-shell -u neo4j -p whatever   # neo4j admin pwd (you changed it)
Connected to Neo4j 3.5.5 at bolt://localhost:7687 as user neo4j.
Type :help for a list of available commands or :exit to exit the shell.
Note that Cypher queries must end with a semicolon.
neo4j> :exit

Bye!
bash-4.4$ exit
>
```

#### Using Cypher Scripts

#### Building, modifying, and searching with Cypher

From the [Introduction to
Cypher](https://neo4j.com/docs/getting-started/current/cypher-intro/):

> Neo4j’s Property Graphs are composed of nodes and relationships, either of
> which may have properties. Nodes represent entities, for example concepts,
> events, places and things. Relationships connect pairs of nodes.
>
> However, nodes and relationships can be considered as low-level building
> blocks. The real strength of the property graph lies in its ability to encode
> patterns of connected nodes and relationships. A single node or relationship
> typically encodes very little information, but a pattern of nodes and
> relationships can encode arbitrarily complex ideas.

Nodes are enclosed in parenthesis and may have variable names, labels, and
properties:

```
()                               # anonymous
(var)                            # variable (scoped to statement)
(:Task)                          # label
(var:Task {status:"READY"})      # properties
```

Relationships are indicated with dashes, `--` for undirected, and `-->` or
`<--` for directed relationships. Like nodes, relationships can have
variables, labels, and properties specified using brackets between the dashes
(e.g. `-[]->`):

```
-->                              # anonymous
-[var]->                         # variable (scoped to statement)
-[:DEPENDS]->                    # label (sometimes referred to as type
-[var:DEPENDS {req:"file.dat"}]  # properties
```

Patterns are combinations of nodes and relationships. A pattern can be assigned
to a variable:

```
next_job = (:Task {name:"start"})-[:DEPENDS]->(:Task {name:"compute0"})
```

Let's work through a small example using `cypher-shell`. This is the [best
place](https://neo4j.com/docs/getting-started/current/cypher-intro/) to start
learing Cypher. We'll create a small _faux_ workflow consisting of one _data
preparation_ node, 3 _compute_ nodes that depend on completion of the prep
node, and a final _analysis_ node that depends on completion of the three
compute nodes.

```sh
neo4j> CREATE (prep:Task {name:"Data Prep", state:"READY"}),
       (crank0:Task {name:"Compute 0", state:"WAITING"}),
       (crank1:Task {name:"Compute 1", state:"WAITING"}),
       (crank2:Task {name:"Compute 2", state:"WAITING"}),
       (viz:Task {name:"Vizualization", state:"WAITING"})

       MERGE (prep)<-[:DEPENDS]-(crank0)
       MERGE (prep)<-[:DEPENDS]-(crank1)
       MERGE (prep)<-[:DEPENDS]-(crank2)
       MERGE (crank0)<-[:DEPENDS]-(viz)
       MERGE (crank1)<-[:DEPENDS]-(viz)
       MERGE (crank2)<-[:DEPENDS]-(viz);
```

Now if we go back to the browser and enter `MATCH (n) RETURN n` in the command
pane we see the following graph. It's not laid out as well as we'd like (maybe
use a subgraph for the three compute nodes?) but the content is correct.

Now that we have a graph, we can add or change properties. Let's say we want to
set the state of the `Data Prep` node to `COMPLETE`:

```sh
neo4j> MERGE (t:Task {name:"Data Prep"})
       SET t.state="COMPLETE"
       RETURN t;
```

Once `Data Prep` is `COMPLETE` we can search for the nodes that depend on it,
with a state of `READY`, and set them to `RUNNING`:

```sh
neo4j> MERGE (t:Task {state:"READY"})-[:DEPENDS]->(Task {name:"Data Prep"})
       SET t.state="RUNNING"
       RETURN t;
```

##### Cleaning Up

You can restart with a clean database (as described above) by stopping the
container, removing the container, deleting the database directory, and
restarting the container. Somewhat easier, when playing around with small
databases, is to delete everything in the database using Cypher:

```sh
neo4j> MATCH(n) WITH n LIMIT 10000 DETACH DELETE n;
```

### Exporting and Importing Databases

Let's build a sample database that represents a BEE workflow. In this case
we'll mimic a simple BLAST job with the Cypher script `blast.cql`:

```sh
CREATE (split:Task {name:"Split Data", state:"READY"}),
       (blast0:Task {name:"Blast 0", state:"WAITING"}),
       (blast1:Task {name:"Blast 1", state:"WAITING"}),
       (data:Task {name:"Collect Data", state:"WAITING"}),
       (err:Task {name:"Collect Errors", state:"WAITING"}),
       (split)<-[:DEPENDS]-(blast0),
       (split)<-[:DEPENDS]-(blast1),
       (blast0)<-[:DEPENDS]-(data),
       (blast1)<-[:DEPENDS]-(data),
       (blast0)<-[:DEPENDS]-(err),
       (blast1)<-[:DEPENDS]-(err);

MATCH (n) RETURN n;
```

We run the script, from within the shell (in the `neo4j` Docker container),
using the `cypher-shell` command:

```sh
bash-4.4$ cat /scripts/blast.cql | cypher-shell -u neo4j -p whatever
n
(:Task {name: "Split Data", state: "READY"})
(:Task {name: "Blast 0", state: "WAITING"})
(:Task {name: "Blast 1", state: "WAITING"})
(:Task {name: "Collect Data", state: "WAITING"})
(:Task {name: "Collect Errors", state: "WAITING"})
bash-4.4$
```

The script creates five nodes and six relationships. The resulting graph is
shown in the screen capture from the Neo4j browser:

![blast graph](blast.png?raw=true)

Here is another example (`hpc.cql`) that may represent a parameter study:

```sh
CREATE (prep:Task {name:"Prepare Data", state:"READY"}),
       (crank0:Task {name:"Compute 0", state:"WAITING"}),
       (crank1:Task {name:"Compute 1", state:"WAITING"}),
       (crank2:Task {name:"Compute 2", state:"WAITING"}),
       (crank3:Task {name:"Compute 3", state:"WAITING"}),
       (crank4:Task {name:"Compute 4", state:"WAITING"}),
       (crank5:Task {name:"Compute 5", state:"WAITING"}),
       (crank6:Task {name:"Compute 6", state:"WAITING"}),
       (crank7:Task {name:"Compute 7", state:"WAITING"}),
       (viz:Task {name:"Visualization", state:"WAITING"}),
       (prep)<-[:DEPENDS]-(crank0),
       (prep)<-[:DEPENDS]-(crank1),
       (prep)<-[:DEPENDS]-(crank2),
       (prep)<-[:DEPENDS]-(crank3),
       (prep)<-[:DEPENDS]-(crank4),
       (prep)<-[:DEPENDS]-(crank5),
       (prep)<-[:DEPENDS]-(crank6),
       (prep)<-[:DEPENDS]-(crank7),
       (crank0)<-[:DEPENDS]-(viz),
       (crank1)<-[:DEPENDS]-(viz),
       (crank2)<-[:DEPENDS]-(viz),
       (crank3)<-[:DEPENDS]-(viz),
       (crank4)<-[:DEPENDS]-(viz),
       (crank5)<-[:DEPENDS]-(viz),
       (crank6)<-[:DEPENDS]-(viz),
       (crank7)<-[:DEPENDS]-(viz);

MATCH (n) RETURN n;
```

Executing this script produces this graph (which will be exported as
`hpc.neo4j`):

![hpc graph](hpc.png?raw=true)

Now, if we want to export the resulting database, we again use the shell and
the `neo4j-admin` command. Neo4j must be stopped to export/import:

```sh
bash-4.4$ neo4j stop
bash-4.4$ neo4j-admin dump --to=/dumps/blast.neo4j
Done: 34 files, 222.4KiB processed.
bash-4.4$ neo4j restart
```

Remember, the `/dumps` directory was mapped to your local filesystem in the
original `docker run` command.

To load the save database into Neo4j, we use `neo4j-admin`. Again, the database
must be stopped to import. The `--force` flag will force the import to
overwrite an existing database.

```sh
bash-4.4$ neo4j stop
bash-4.4$ neo4j-admin load --from=/dumps/blast.neo4j --force
Done: 34 files, 222.4KiB processed.
bash-4.4$ neo4j restart
```

### Programmatic Interaction with Python
```sh
> git clone ...              # clone this repo
> cd neo4j
> python3 -m venv ./venv     # must be Python > 3.3
> source ./venv/bin/activate
(venv) > pip install --upgrade pip
(venv) > pip install neo4j
(venv) > deactivate          # when you're done messing around
```

## References

* [Run Neo4j in Docker](https://neo4j.com/developer/docker-run-neo4j/)

