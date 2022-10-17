/* 
 * This file comtains several objects for components in our app
 *
 *
 * */

components = new Map()
buttons = new Map()
// The current content displayed in the main window
currentContent = null

const wf = require('./workflows.js')
const config = require('./config.js')

// Add extra buttons unrelated to a component
// Setup start button
function startButton(button_id) {
	button = document.getElementById(button_id);
	// Create a click method listener for the button
	button.addEventListener('click', e => {	
		wf.start_workflow();
        document.getElementById('start-wf_button').style.display = "none";
        document.getElementById('pause-wf_button').style.display = "inline";
	})
}

// Setup pause button
function downloadButton(button_id) {
	button = document.getElementById(button_id);
	// Create a click method listener for the button
	button.addEventListener('click', e => {	
        // Breaks seperations of concerns add to button map and lookup
        console.log('Downloading')
		wf.download_current_archive();
	})
}


// Setup pause button
function pauseButton(button_id) {
	button = document.getElementById(button_id);
	// Create a click method listener for the button
	button.addEventListener('click', e => {	
        // Breaks seperations of concerns add to button map and lookup
		wf.pause_workflow();
        document.getElementById('pause-wf_button').style.display = "none";
        document.getElementById('resume-wf_button').style.display = "inline";
	})
}

// Add extra buttons unrelated to a component
// Setup start button
function resumeButton(button_id) {
	button = document.getElementById(button_id);
	// Create a click method listener for the button
	button.addEventListener('click', e => {	
		wf.resume_workflow();
        document.getElementById('resume-wf_button').style.display = "none";
        document.getElementById('pause-wf_button').style.display = "inline";
	})
}


function updateButton(button_id) {
	button = document.getElementById(button_id);
	// Create a click method listener for the button
	button.addEventListener('click', e => {	
		wf.update_current_workflow();
	})
}

class Component {
    constructor(content_id, button_id, form_button_id) {
        this.content_id = content_id;
        this.element = document.getElementById(content_id);
        // Add to components map
        components.set(content_id, this.element);
        // Setup our button if we have one
        if (button_id !== null) {
            this.button_id = button_id;
            this.button = document.getElementById(this.button_id);
            // Add button to buttons map keyed on it's ID
            buttons.set(this.button_id, this.button);
            // Setup an event listener for when the button is clicked
            this.setupButtonListener();
        }
        // Setup form if we have one
        if (form_button_id !== null) {
            this.form_button_id = form_button_id;
            // Get for button element then attach a listener to it
            this.form = document.getElementById(this.form_button_id);
            this.setupFormListener();
        }
    }

    // Event listener for a form if the component has one
    // Every component except welcomeMessage has one
    // This is an abstract method 
    setupFormListener() {
        throw new Error("Form listener needs to be implemented in child class");
    }
    
    // Listener for the left menu button. Toggles the main content with the 
    // specific menu and sets its button to active.
    setupButtonListener() {
        // Create a click method listener for the button
        if (this.button) {
            this.button.addEventListener('click', e => {
                // Toggle the component on or off and toggle the associated button
                this.toggle_content();
                // this.toggle_button(add_wf_button, main_button_set)
                this.toggle_button();
            })
        }
    }

    // Toggle the component on or off
    toggle_content() {
        if (this.element.style.display === 'inline'){
            this.element.style.display = 'none';
            // Return to main window
            currentContent.style.display = 'inline';
        }
        else {
            let temp_components = new Map(components)
            temp_components.delete(this.component_id);
            for (let component of components.values()) {
                component.style.display = 'none';
            }
            this.element.style.display = 'inline';
            currentContent.style.display = 'none';
        }

    }

    // This highlights the button of the associated component when it is active
    toggle_button() {
        if (this.button.classList.contains('is-active')) {
            this.button.classList.remove("is-active");
        }
        else {
            // Create a button map and remove the current button from it
            let temp_buttons = new Map(buttons);
            temp_buttons.delete(this.button_id);
            // Iterate through the button objects
            for (let button of temp_buttons.values()) {
                if (button.classList.contains("is-active")) {
                    button.classList.remove("is-active");
                }
            }

            this.button.classList.add("is-active");
        }
    }
}



class AddWorkflow extends Component {
    constructor(content_id, button_id, form_button_id) {
        super(content_id, button_id, form_button_id);
    }

    // Gets the workflow directory path 
    //get_actual_path(full_path, rel_path) {
    //    let parent_dir = rel_path.split('/')[0];
    //    let stopping_point = full_path.indexOf(rel_path) + parent_dir.length;
    //    let actual_path = full_path.slice(0, stopping_point);
    //    return actual_path;
    //}

    setupFormListener() {
        this.form.addEventListener('click', async e => {
            // Need to add checking for valid values
            // Get all the form contents then pass to add workflow function
            let name = document.getElementById('add-wf_name').value;
            let main_cwl = document.getElementById('add-wf_cwl').value;
            let yaml = document.getElementById('add-wf_yaml').value;
            let tarball_path = document.getElementById('add-wf_tar').files[0].path;
            wf.add_workflow(name, main_cwl, yaml, tarball_path);
            // Reset the form
            document.getElementById('add-workflow_form').reset();
            document.getElementById('start-wf_button').style.display = "inline";
            document.getElementById('pause-wf_button').style.display = "none";
            document.getElementById('resume-wf_button').style.display = "none";
            hideWelcome();
            this.toggle_content();
            this.toggle_button()
        })
    }
}

class Settings extends Component {
    constructor(content_id, button_id, form_button_id) {
        super(content_id, button_id, form_button_id);
    }

    setupFormListener() {
        this.form.addEventListener('click', e => {
            let moniker = document.getElementById('settings-moniker').value;
            let bolt_port = document.getElementById('settings-bolt_port').value;
            let wfm_port = document.getElementById('settings-wfm_port').value;
            config.init(moniker, bolt_port, wfm_port); 
            this.toggle_content();
            this.toggle_button();
        })
    }

}


class DeleteWorkflow extends Component {
    constructor(content_id, button_id, form_button_id) {
        super(content_id, button_id, form_button_id);
    };

    setupFormListener() {
        this.form.addEventListener('click', e => {
            let wf_id = document.getElementById('delete-wf_id').value;
            wf.delete_workflow(wf_id);
            showWelcome();
            document.getElementById('delete-workflow_form').reset();
            this.toggle_content();
            this.toggle_button();
            document.getElementById('start-wf_button').style.display = "inline";
            document.getElementById('pause-wf_button').style.display = "none";
            document.getElementById('resume-wf_button').style.display = "none";
        })
    }

}

class ReexecuteWorkflow extends Component {
    constructor(content_id, button_id, form_button_id) {
        super(content_id, button_id, form_button_id);
    }

    setupFormListener() {
        // wf.add_workflow()
        this.form.addEventListener('click', async e => {
            // Get all the form contents then pass to add workflow function
            let name = document.getElementById('reexecute-wf_name').value;
            let tarball_path = document.getElementById('reexecute-wf_tar').files[0].path;
            wf.reexecute_workflow(name, tarball_path)
            document.getElementById('reexecute-workflow_form').reset();
            hideWelcome();
            document.getElementById('start-wf_button').style.display = "inline";
            document.getElementById('pause-wf_button').style.display = "none";
            document.getElementById('resume-wf_button').style.display = "none";
            this.toggle_content();
            this.toggle_button()
        })
    }

}



function initContent() {
    currentContent = components.get("welcomeMessage")
}

// Component factory 
function addComponent(content_id, button_id = null, form_button_id = null) {
    switch(content_id) {
        case 'addWorkflow':
            component = new AddWorkflow(content_id, button_id, form_button_id)
            break
        case 'deleteWorkflow':
            component = new DeleteWorkflow(content_id, button_id, form_button_id)
            break;
        case 'reexecuteWorkflow':
            component = new ReexecuteWorkflow(content_id, button_id, form_button_id)
            break; 
        case 'settings':
            component = new Settings(content_id, button_id, form_button_id)
            break;
        default:
            // welcomeMessage and currentWorkflow just use Component
            component = new Component(content_id, button_id, form_button_id)
    }
}

function hideWelcome() {
    currentContent = document.getElementById('currentWorkflow')
}

function showWelcome() {
    currentContent = document.getElementById('welcomeMessage')
}


module.exports = { Component, addComponent, startButton, downloadButton, pauseButton, hideWelcome, 
                   resumeButton, updateButton, initContent, hideWelcome, showWelcome }
