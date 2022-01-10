/*
 *
 *
 *
 */ 
const sqlite3 = require('sqlite3').verbose();

function initialize() {
    // If the DB doesn't exist create it
    let db = new sqlite3.Database('app.db', sqlite3.OPEN_READWRITE, (err) => {
        if (err) {
            console.error(err.message);
        }
    });

}

function close() {
    db.close((err) => {
        if (err) {
          return console.error(err.message);
        }
         console.log('Close the database connection.');
    });
}

function add_wf(wf_id) {
        let completed = 'False';
        let archived = 'False';
        let percentage_complete = 0;
        let status = 'Pending';
        let sql = `INSERT INTO workflows (wf_id, completed, archived, percentage_complete, status)
                   VALUES(?, ?, ?, ?, ?)`;
        let entries = [wf_id, completed, archived, percentage_complete, status];

        db.run(sql, entries, (err) => {
            if (err) {
                // Need to create diaolgue for user
                return console.error(err.message);
            }
            console.log(`Added workflow!`);
        });
}

function delete_wf() {
    
}

function add_task(wf_id, location, description) {
        var completed = 'False'
        var status = 'Pending'
        let sql = `INSERT INTO tasks (wf_id, completed, location, description, status)
                VALUES(?, ?, ?, ?, ?)`
        let entries = [wf_id, completed, location, description, status];
        db.run(sql, entries, (err) => { 
             if (err) {
                // Need to create diaolgue for user
                return console.error(err.message)
            }
            console.log(`Added task!`);
        });
}

function delete_task(wf_id, task_id) {

}
