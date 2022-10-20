const Database = require('better-sqlite3')
//const sql = require('sqlite3')
const fs = require('fs')

let db = null

function init() {
    // If the DB doesn't exist create it
    db = new Database('data/app.db', { verbose: console.log });
    // Create tables if they don't exist
    const workflow_stmt = db.prepare(`
            CREATE TABLE IF NOT EXISTS workflows (
                id INTEGER PRIMARY KEY,
                -- Set workflow ID to unique.
                wf_id INTEGER UNIQUE,
                name TEXT,
                completed BOOLEAN,
                archived BOOLEAN,
                percentage_complete FLOAT,
                status TEST NOT NULL
            );`);
    
    const task_stmt = db.prepare(`
			CREATE TABLE IF NOT EXISTS tasks (
				id INTEGER PRIMARY KEY,
				wf_id INTEGER NOT NULL,
				task_id INTEGER UNIQUE,
				completed BOOLEAN,
				resource TEXT,
				status TEXT,
                name TEXT,
				base_command TEXT,
				FOREIGN KEY (wf_id)
					REFERENCES workflows (wf_id)
						ON DELETE CASCADE
						ON UPDATE NO ACTION
			);`);

    const config_stmt = db.prepare(`
			CREATE TABLE IF NOT EXISTS config (
				id INTEGER PRIMARY KEY,
                hostname TEXT,
                moniker TEXT,
                resource TEXT,
                bolt_port INTEGER,
                wfm_sock TEXT
          );`);

    const wf_info = workflow_stmt.run();
    const task_info = task_stmt.run();
    const config_info = config_stmt.run();
}

// Add a WF
function add_wf(wf_id, name) {
    let completed = 'False';
    let archived = 'False';
    let percentage_complete = 0;
    let status = 'Pending';
    const stmt = db.prepare(`INSERT INTO workflows (wf_id, completed, archived, 
									percentage_complete, status, name)
               						VALUES(?, ?, ?, ?, ?, ?)`);
	const info = stmt.run(wf_id, completed, archived, 
                          percentage_complete, status, name);
}

function add_config(hostname, moniker, resource, bolt_port, wfm_sock) {
    const stmt = db.prepare(`INSERT INTO config (hostname, moniker, resource, bolt_port, wfm_sock)
                            VALUES(?, ?, ?, ?, ?)`);
    const info = stmt.run(hostname, moniker, resource, bolt_port, wfm_sock);
}


// Get a parituclar wf 
function get_wf(wf_id) {
    const stmt = db.prepare('SELECT * FROM workflows WHERE wf_id=?');
    const wf = stmt.get(42);
    return wf;
}

// Get all workflows in the system
function get_workflows() {
    const stmt = db.prepare('SELECT * FROM workflows');
    const wf = stmt.all();
    return wf; 
}

// Get all tasks associated with a wf_id
function get_tasks(wf_id) {
    const stmt = db.prepare('SELECT * FROM tasks WHERE wf_id=?');
    const tasks = stmt.all(wf_id);
    return tasks; 
}

function update_task_state(task_id, wf_id, status) {
    const stmt = db.prepare(`UPDATE tasks
                             SET status=?
                             WHERE task_id=? AND wf_id=? VALUES(?, ?, ?)`);
    const task_info = stmt.run(status, task_id, wf_id);
}


function delete_wf(wf_id) {
    let stmt = db.prepare('DELETE FROM workflows WHERE wf_id=?');
    const info = stmt.run(42);
}

function add_task(task_id, wf_id, name, resource, base_command, status) {
    const completed = 'False';
    const stmt = db.prepare(`INSERT INTO tasks (wf_id, task_id, completed, 
            resource, base_command, status, name) VALUES(?, ?, ?, ?, ?, ?, ?)`);
    const task_info  = stmt.run(wf_id, task_id, completed, resource, base_command, status, name);
    console.log(task_info);
}

function delete_task(wf_id, task_id) {
    let sql = `DELETE FROM  workflows
               WHERE task_id=task`;
}

function close() {
    db.close((err) => {
        if (err) {
          return console.error(err.message);
        }
         console.log('Close the database connection.');
    });
}

module.exports = { init, add_wf, get_wf, get_workflows, get_tasks, delete_wf, 
                   add_config, add_task, delete_task }
