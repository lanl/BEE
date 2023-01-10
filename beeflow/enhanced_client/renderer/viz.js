// const {NeoVis} = require('neovis.js');

let initialized = false;

function draw(containerId, boltPort) {
  var config = {
    containerId,
    neo4j: {
      serverUrl: `bolt://127.0.0.1:${boltPort}`,
      serverUser: "neo4j",
      serverPassword: "password",
    },
  }
  var cypher = {
    labels: {
      "Task": {
        label: "name"
      },
      "Metadata": {
        label: "state"
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
    initialCypher: "MATCH p=()-[r:DEPENDS_ON|:DESCRIBES]->() RETURN p",
  };

  var final = {
    ...config,
    ...cypher
  };
  var viz = new NeoVis.default(final);
  viz.render();
  initialized = true;
}

module.exports = { draw };
