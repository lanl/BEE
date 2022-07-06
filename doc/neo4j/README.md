# Experiments with Neo4j Graph Database

This repository contains some basic notes on how to use Neo4j as it relates to
the BEE project (our machines, our specific goals, etc.). The repo will evolve
over time as I gain experience and add more tests and examples. If you find
problems, or want to add something, hack away and submit a pull request!

## Getting Started

### Running Neo4j with Docker

It's easy to experiment with Neo4j if you have access to a machine that can run
Docker. Do it the easy way, on your Mac, with Docker installed, or using the 
unpriviledged in Charliecloud on a cluster. 
Or, do it the hard way, on Darwin with Al's Packer VM or a Vagrant box with Docker
provisioned.

```sh
> docker run --publish=7474:7474 --publish=7687:7687 --name neo4j --volume=$HOME/neo4j/data:/data neo4j
```

The directory mapped to `/data` is where the database (data, config, etc.) will
live. As far as I can tell, Neo4j can only support a single database. The
`--name` flag specifies the name of the container. The `neo4j` at the end of
the command is the image name (which will be fetched from Docker Hub if not
already downloaded).

![Neo4j browser][browser]

In a local browser, go to `http://localhost:7474/browser/`. If you're starting
with a brand new database, you'll be asked to change the password for the admin
(`neo4j`) account after getting past the default password prompt (also
`neo4j`). The browser provides a nice interface for administering the database
(users, etc.) and experimentation. Interface panes accept textual commands that
interact with the database. 

![browser interface panes][pane]

The language used is called Cypher (the same language can be used from a shell
as described later). Results of Cypher commands are shown in the browser as
text or with a graphical representation.

![visual display of graph][graph]

### Pausing or Terminating Neo4j with Docker

If you want to pause and resume the Neo4j container, use `docker stop` and
`docker start`:

```sh
> docker stop neo4j
...
> docker start neo4j
```

If you need to restart the container, you'll first need to delete the old
one. Docker won't let you start a container with the same name:

```sh
> docker stop neo4j
> docker rm neo4j
> docker run --publish=7474:7474 --publish=7687:7687 --name neo4j --volume=$HOME/neo4j/data:/data neo4j
```

The above will restart the container with the existing database that's stored
in the mapped directory (`/data`). If you want to start clean, remove that
directory:

```sh > docker stop neo4j
> docker rm neo4j
> rm -rf $HOME/neo4j/data     # or whatever you called yours
> docker run --publish=7474:7474 --publish=7687:7687 --name neo4j --volume=$HOME/neo4j/data:/data neo4j
```

### Running Neo4j with Charliecloud 
You can run Neo4j on LANL platforms (e.g. fog) using Charlecloud.

#### Building using Docker
First, on a system with Docker and Charliecloud installed, you'll need to pull the Neo4j image
and create a Charliecloud tarball:

```sh
> docker pull neo4j
> ch-docker2tar neo4j /var/tmp
```

#### Building using Charliecloud ch-grow 
On a system without Docker, that has Charliecloud installed, you'll need to build 
Neo4j with Charliecloud's unpriviledged build.  Note: You may need to install 
lark-parser in your python environment. The files in the ch-grow-files directory
(Dockerfile.neo4j, environment, and ch-run-neo4j.sh) need to be in your current 
directory, this should be where you want to place the charliecloud tarball.

```sh
ch-grow -t neo4j-ch .
ch-builder2tar -b ch-grow neo4j-ch .
```
If you have created the tarball using Charlicloud ch-grow see the notes below for
fixing the configuration files then using the following commands to run neo4j from
the tarball.
```sh
mkdir /var/tmp/<username>
ch-tar2dir neo4j-ch.tar.gz /var/tmp/<username>/
ch-run -w -b /home/<username>/neo4j-conf/:/var/lib/neo4j/conf/ /var/tmp/<username>/neo4j-ch/ -- /ch-run-neo4j.sh
```


Now copy the resulting tarball to the LANL system of choice. At this point you
no longer need Docker, only Charliecloud.

On the target system, you'll need to set up some directories and a
configuration file so multiple uses can run and connect to Neo4j
simultaneously:

```sh
> mkdir /var/tmp/username
> mkdir ~/neo4j-conf
```

Untar Neo4j into your `/var/tmp` directory:

```sh
> ch-tar2dir neo4j.tar.gz /var/tmp/username
```

Copy and edit Neo4j's default configuration file:

```sh
> cp /var/tmp/username/neo4j-ch/var/lib/neo4j/conf/neo4j.conf ~/neo4j-conf/
> vi ~/neo4j-conf/neo4j.conf

...Change these lines...

# Bolt connector
dbms.connector.bolt.enabled=true
#dbms.connector.bolt.tls_level=OPTIONAL
# EDIT PORT BELOW #
#dbms.connector.bolt.listen_address=:7687

# HTTP Connector. There can be zero or one HTTP connectors.
dbms.connector.http.enabled=true
# EDIT PORT BELOW #
#dbms.connector.http.listen_address=:7474

# HTTPS Connector. There can be zero or one HTTPS connectors.
dbms.connector.https.enabled=true
# EDIT PORT BELOW #
#dbms.connector.https.listen_address=:7473

...to uncomment the port assignment and change them to unique values...

# Bolt connector
dbms.connector.bolt.enabled=true
#dbms.connector.bolt.tls_level=OPTIONAL
# EDIT PORT BELOW #
dbms.connector.bolt.listen_address=:17687

# HTTP Connector. There can be zero or one HTTP connectors.
dbms.connector.http.enabled=true
# EDIT PORT BELOW #
dbms.connector.http.listen_address=:17474

# HTTPS Connector. There can be zero or one HTTPS connectors.
dbms.connector.https.enabled=true
# EDIT PORT BELOW #
dbms.connector.https.listen_address=:17473
```

Now you can start Neo4j using Charliecloud:

```sh
> ch-run -w --set-env=/var/tmp/username/neo4j-ch/environment -b /users/username/neo4j-conf/:/var/lib/neo4j/conf/ /var/tmp/username/neo4j-ch/ -- neo4j console
/bin/bash: warning: setlocale: LC_ALL: cannot change locale (en_US.UTF-8)
bash: warning: setlocale: LC_ALL: cannot change locale (en_US.UTF-8)
Active database: graph.db
Directories in use:
  home:         /var/lib/neo4j
  config:       /var/lib/neo4j/conf
  logs:         /var/lib/neo4j/logs
  plugins:      /var/lib/neo4j/plugins
  import:       /var/lib/neo4j/import
  data:         /var/lib/neo4j/data
  certificates: /var/lib/neo4j/certificates
  run:          /var/lib/neo4j/run
Starting Neo4j.
2019-09-11 20:58:18.057+0000 INFO  ======== Neo4j 3.5.9 ========
2019-09-11 20:58:18.069+0000 INFO  Starting...
2019-09-11 20:58:19.925+0000 INFO  Bolt enabled on 127.0.0.1:17687.
2019-09-11 20:58:21.354+0000 INFO  Started.
2019-09-11 20:58:22.352+0000 INFO  Remote interface available at http://localhost:17474/
```

In order to remotely browse the database with a web browser you'll need to forward a
couple of ports **AFTER** you've started Neo4j:

```sh
> ssh -L 17474:localhost:17474 -L 17687:localhost:17687 -l username fg-fey.lanl.gov
```

Now you should be able to connect remotely by pointng your browser at
`localhost:17474`. Remember, the ports you use will be **uniue to you** (as set in
the `neo4j.conf` file).

## Interacting with the Database

The Cypher language is used to interact with the graph database (add/delete
nodes and relationships, search, etc.). As shown above, you can experiment with
Cypher using panes in the browser window. If you need to do more than
experiment, it's probably best to use Cypher (and Cypher scripts) from the
command line or to interact programmatically using Python.

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

We can use Docker to start a shell in the running Neo4j container and then run
`cypher-shell` to access Cypher:

```sh
> docker exec -it neo4j bash      # neo4j from --name on docker run
bash-4.4# cypher-shell -u neo4j -p whatever   # neo4j admin pwd (you changed it)
Connected to Neo4j 3.5.5 at bolt://localhost:7687 as user neo4j.
Type :help for a list of available commands or :exit to exit the shell.
Note that Cypher queries must end with a semicolon.
neo4j> :exit

Bye!
bash-4.4# exit
>
```

At some pointy you'll likely want to map in a directory that contains your
accumulated Cypher scripts. You can mount it with the `docker run` command
(remember, you'll need to `docker rm neo4j` to restart the container):

```sh
> docker stop neo4j
> docker rm neo4j
> docker run --publish=7474:7474 --publish=7687:7687 --name neo4j --volume=$HOME/neo4j/data:/data --volume $HOME/BEE/database/neo4j:/scripts neo4j
> docker exec -it neo4j bash      # neo4j from --name on docker run
bash-4.4# ls /scripts
README.md  img        venv
>
```

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

![graph of five node workflow][5node]

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

In another shell, run Neo4j using Docker. Do it the easy way, on your Mac, with
Docker installed. Or, do it the hard way, on Darwin with Al's Packer VM or a
Vagrant box with Docker provisioned.


## References

* [Run Neo4j in Docker](https://neo4j.com/developer/docker-run-neo4j/)

[pane]:img/cypher_pane.png
[graph]:img/graph_pane.png
[browser]:img/neo4j_browser.png
[5node]:img/5node.png

