const neo4j = require('neo4j-driver');

function run() {
  const uri = 'bolt://127.0.0.1:34273';
  const driver = neo4j.driver(uri, neo4j.auth.basic('neo4j', 'password'));
  const session = driver.session();

  session.run('MATCH (n) RETURN n')
    .then(result => {
      console.log(result);
    })
    .catch(err => {
      console.log(err);
    })
    .finally(() => {
      session.close();
      driver.close();
    });
}

module.exports = { run };
