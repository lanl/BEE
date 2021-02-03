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

