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

class Component {
    constructor(content_id, button_id, form_id) {
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
        if (form_id !== null) {
            this.form_id = form_id;
            // Get for button element then attach a listener to it
            this.form = document.getElementById(this.form_id);
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
    constructor(content_id, button_id, form_id) {
        super(content_id, button_id, form_id);
    }

    // Gets the workflow directory path 
    get_actual_path(full_path, rel_path) {
        let parent_dir = rel_path.split('/')[0];
        let stopping_point = full_path.indexOf(rel_path) + parent_dir.length;
        let actual_path = full_path.slice(0, stopping_point);
        return actual_path;
    }

    setupFormListener() {
        // wf.add_workflow()
        this.form.addEventListener('click', e => {
            // Get all the form contents then pass to add workflow function
            let name = document.getElementById('add-wf_name').value;
            let cwl = document.getElementById('add-wf_cwl').value;
            let yaml = document.getElementById('add-wf_yaml').value;
            let tarball_path = document.getElementById('add-wf_tar').files[0].path;
            //let inputs = [name, cwl, yaml, tarball]
            //let empty = false
            //let i;
            //for (i = 0; i < inputs.length; i++) {
            //    if (inputs[i].value.length < 1) {
            //       empty = true;
            //       break;
            //    }
            //}
            //if (empty) {
            //    alert('Need to fill all fields');
            //    return;
            //}

            // //let locations = document.getElementById('add-wf_locations').value;
            // // Get the directory 
            // let directory = document.getElementById('add-wf_directory').files[0];
            // if (directory == undefined) {
            //     empty = true;
            // }

            // console.log(directory)
            // let full_path = directory.path;
            // let rel_path = directory.webkitRelativePath;
            // let actual_path = this.get_actual_path(full_path, rel_path);
            wf.add_workflow(name, cwl, yaml, tarball_path);
            // Reset the form
            document.getElementById('add-workflow_form').reset();
            //this.form.reset();
            this.toggle_content();
        })
    }
}

class DeleteWorkflow extends Component {
    constructor(content_id, button_id, form_id) {
        super(content_id, button_id, form_id);
    }

    setupFormListener() {
        // wf.add_workflow()
        this.form.addEventListener('click', e => {
            // Get all the form contents then pass to add workflow function
            let wf_id = document.getElementById('add-wf_name').value;
            wf.delete_workflow(wf_id)
        })
    }

}

class ArchiveWorkflow extends Component {
    constructor(content_id, button_id, form_id) {
        super(content_id, button_id, form_id);
    }

    setupFormListener() {
        // wf.add_workflow()
        this.form.addEventListener('click', e => {
            // Get all the form contents then pass to add workflow function
            let wf_name = document.getElementById('add-wf_name').value;
            let wf_cwl = document.getElementById('add-wf_cwl').value;
            let wf_locations = document.getElementById('add-wf_locations').value;
            let wf_directory = document.getElementById('add-wf_directory').files[0];
            let full_path = wf_directory.path;
            let rel_path = wf_directory.webkitRelativePath
            let actualPath = this.get_actual_path(full_path, rel_path)
            wf.add_workflow(wf_name, cwl_file, locations, actual_path)
            console.log(wf_name, wf_cwl, wf_locations, actualPath)
        })
    }

}


class Settings extends Component {
    constructor(content_id, button_id, form_id) {
        super(content_id, button_id, form_id);
    }

    setupFormListener() {
        // wf.add_workflow()
        this.form.addEventListener('click', e => {
            // Get all the form contents then pass to add workflow function
            // Getting the form contents requires hardcoding the ids of the 
            // form elements in here which I'm not very happy with since it 
            // breaks seperation of concerns
            let wf_name = document.getElementById('add-wf_name').value;
            let wf_cwl = document.getElementById('add-wf_cwl').value;
            let wf_locations = document.getElementById('add-wf_locations').value;
            let wf_directory = document.getElementById('add-wf_directory').files[0];
            let full_path = wf_directory.path;
            let rel_path = wf_directory.webkitRelativePath
            let actualPath = this.get_actual_path(full_path, rel_path)
            wf.add_workflow(wf_name, cwl_file, locations, actual_path)
            //console.log(wf_name, wf_cwl, wf_locations, actualPath)
        })
    }

}

function initContent() {
    currentContent = components.get("welcomeMessage")
}

// Component factory 
function addComponent(content_id, button_id = null, form_id = null) {
    switch(content_id) {
        case 'addWorkflow':
            component = new AddWorkflow(content_id, button_id, form_id)
            break
        case 'deleteWorkflow':
            component = new DeleteWorkflow(content_id, button_id, form_id)
            break;
        case 'archiveWorkflow':
            component = new ArchiveWorkflow(content_id, button_id, form_id)
            break; 
        case 'settings':
            component = new Settings(content_id, button_id, form_id)
            break;
        default:
            // welcomeMessage and currentWorkflow just use Component
            component = new Component(content_id, button_id, form_id)
    }
}


module.exports = { Component, addComponent, initContent }
