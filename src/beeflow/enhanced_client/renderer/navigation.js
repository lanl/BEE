/*
 * Navbar settings
 *
 * /



class Navbar {
    constructor(wf_list) {
        this.wf_list = document.getElementById(wf_list)
    }

    // Add workflow to workflow list
    add(workflow) {
        workflow = workflows.get(wf_id)
        let item = document.createElement("li")
        item.innerHTML = "<a>" + workflow.name + "</a>"
        item.className = "is-size-1"
        nav_workflows.append(item)

    }

    // Remove workflow from workflow list
    remove(workflow) {
    
    }
}
