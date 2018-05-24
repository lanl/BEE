## Build and Execute Environment (BEE) User Guide for `BeeFlow`

The following guide shows you how to run `BeeFlow` on HPC environment.

### Installation

If this is your first time using BEE, follow the installation part of BEE-Charliecloud, BEE-VM, BEE-AWS, or BEE-OpenStack to install and configure BEE. You may need to refer to the specific guide depending on the platform you intend to use.


### Launch BeeFlow task

##### Step 1. Configure beefile
Configure `<task_name>.beefile` file for each task in the workflow. Make sure the working directory matches if you want two tasks sharing data through the filesystem. Detailed guide for configuring beefile can be found in the guide for launching single task on a specific platform.

##### Step 2. Configure beeflow file
The beeflow file contains a list of tasks in the workflow in JSON format. Each entry corresponds to one task. In each entry, the task name and its dependencies are stored. 

For example, we have three tasks: Task A, Task B, and Task C. Task B must wait until Task A finishes before it can start (off-line dependency). Task C can start as soon as Task B starts. The beeflow file should be composed as follows:

````
{
    "Task A": {
	"dependency_list" : [] 
    },
    "Task B": {
		"dependency_list": ["Task A"],
		"dependency_mode": "off-line"
    },
    "Task C": {
		"dependency_list": ["Task B"],
		"dependency_mode": "in-situ"
    }
}

````

##### Step 2. Launch workflow
* a. Prepare run scripts as necessary.
* b. Open `2` console windows. One serves as daemon control; another serves as client control.
* c. Run `bee_orc_ctl.py` on daemon control window to start BEE daemon. The daemon is necessary for keeping the launching, running, and monitoring processes running. So, running it in an ordinary shell session can cause unexpected shutdown due to shell session timeout or disconnection. For long term execution, it is recommended to run the daemon on a separated `screen`. For details of using `screen`, please refer to this [tutorial](https://www.rackaid.com/blog/linux-screen-tutorial-and-how-to/).

* d. Run the BeeFlow launcher on client control window to launch BeeFlow:
  * `bee_composer.py -f <workflow_name>`   
Runs the workflow specified by \<workflow_name\>.beeflow (needs to be in the current directory).
  
### Example BeeFlow with off-line dependency
We use BLAST as an example to show how to launch a traditional workflow with BeeFlow. The dependencies in the workflow are illustrated below. 

![](https://raw.githubusercontent.com/lanl/BEE_Private/jieyang-dev/doc/figures/blast-dag.jpg?token=ABmT_ZEKIl0Z-NZXBj7vVcfINpi3580rks5bA0SqwA%3D%3D)

We first need to prepare a beefile and run script for each component in the workflow. All files can be found in `examples/bee-composer-example/blast`. Then we compose the beeflow file.

Assume we use two BLAST workers, the beeflow file should be:

````
{
    "blast-split": {
		"dependency_list" : [] 
    },
    "blast-worker001": {
		"dependency_list": ["blast-split"],
		"dependency_mode": "off-line"
    },
    "blast-worker002": {
    	"dependency_list": ["blast-split"],
	"dependency_mode": "off-line"
    },
    "blast-output": {
        "dependency_list": ["blast-worker001",
        						"blast-worker002"],
        "dependency_mode": "off-line"
    }
}

````

### Example BeeFlow with in-situ dependency
We use the workfow containing Vector Particle-In-Cell (VPIC) and ParaView as an example to show how to launch an in-situ workflow with BeeFlow. The dependencies in the workflow are illustrated below. 

![](https://raw.githubusercontent.com/lanl/BEE_Private/jieyang-dev/doc/figures/vpic-dag.jpg?token=ABmT_eQtKH9nU-GfjIExHNo3JW-jey40ks5bA0TYwA%3D%3D)

We first need to prepare  a beefile and run script for each component in the workflow. All files can be found in `examples/bee-composer-example/vpic-paraview`. Then we compose the beeflow file.

We use the filesystem (disk-based) to share data between VPIC and ParaView server. The ParaView client runs on the user's local machine, so it is should be started manually and not included in BeeFlow orchestration. The beeflow file is:

````
{
    "vpic": {
	"dependency_list" : [] 
    },
    "paraview-server": {
	"dependency_list": ["vpic"],
	"dependency_mode": "in-situ"
    }
}
````


 

   







