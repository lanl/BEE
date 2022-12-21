let initialized = false;

function draw() {
  var config = {
    container_id: "viz",
    server_url: "bolt://localhost:9995",
    server_user: "neo4j",
    server_password: "password"
  }
  var cypher = {
    labels: {
      "Task": {
        caption: "name"
      },
      "Metadata": {
        caption: "state"
      },
    },
    relationships: {
      "DEPENDS_ON": {
        caption: true,
      },
      "DESCRIBES": {
        caption: false
      },
    },
    hierarchical: true,
    hierarchical_sort_method: "directed",
    randomSeed: 0,
    initial_cypher: "MATCH p=()-[r:DEPENDS_ON|:DESCRIBES]->() RETURN p",
  };

  var final = {
    ...config,
    ...cypher
  };
  var viz = new NeoVis.default(final);
  viz.render();
  initialized = true;
}
