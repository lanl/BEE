## VPIC-ParaView Example
This example (vpic-paraview) requires interaction with the ParaView client on the user's desktop (or laptop, referred to as desktop from here). These instructions show how to connect the ParaView client to a remote ParaView server running on a cluster. 

* The example is tested with ParaView 5.2.0.

#### Step 1. Launch the BeeFlow example.
Launch instructions can be found in ../../../doc/User Guide for BeeFlow.md.  If the launch is successful, the user should see two kinds of output. One is the output from VPIC. Another is the ParaView server, which should be looks like:

	- Connection URL: cs://paraview-server-bee-master:11111
	- Accepting connection(s): paraview-server-bee-master:11111
	
   Since VPIC continues to log timestep information, the output of the ParaView server may get pushed out of the console, so please check it by scrolling back through console output. 

#### Step 2. Setup the ssh tunnel:
To setup the ssh tunnel from the user’s desktop to the remote ParaView server (on port 11111 by default). 

1. If `bee_orc_ctl.py` is running on one of the compute nodes of the cluster, two ssh tunnels will need setup. Run the following command in a new terminal (on the user's desktop):

		`ssh -L 11111:localhost:11111 <username>@<host>`	
    
   Continue in the same window; run the following command; keep the terminal open (to keep the ssh session alive).
           
		`ssh -L 11111:localhost:11111 <username>@<node_name>` 

2. If `bee_orc_ctl.py` is running on the front-end of the cluster, only one ssh tunnel needs to be setup. Run the following command in a new terminal and keep it open (this keeps the ssh session alive).

		`ssh -L 11111:localhost:11111 <username>@<host>`

Now port 11111 on the user's desktop is forwarded to the port 11111 on the machine where the ParaView server is running. 

#### Step 3. ParaView on the User's Desktop:
	1. Open the ParaView client on the user's desktop and click ‘connect’ (third button, first row).
	2. In the pop-up window ('Choose Server Configuration'), click ‘Add Server’. 
	3. Fill in the following:
		- Name: `beeflow_example`
		- Server Type: `Client/Server`
		- Host: `localhost`
		- Port: `11111` 
	4. Select 'Configure'.
	5. Leave Startup Type as ‘Manual’ and click ‘Save’. 
	6. Select the server just added and click ‘connect’. Wait for a few seconds to see,
      ‘Client connected.’ in the console where `bee_orc_ctl.py` is running.

5. In-situ visualization of data files through the ParaView client. 
	1. Click ‘Open’ (first button on the first row). 
	2. Select directory in ‘/mnt/docker_share/my_test’. 
		- This is where VPIC is writing result files. 
	3. Select any of the output files (*.pvtp or *.vtp) and click ‘ok’ to view them. 
		- Click the eye-shaped button next to the file in the Pipeline Browser to make objects viewable.
