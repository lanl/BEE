## Build and Execute Environment (BEE) User Guide for `BeeSwarm`

The following guide shows you how to run `BeeSwarm` to enable scalability test in Continuous Integration. `BeeSwarm` currently support Travis CI with scalability test on Chameleon cloud. More platforms will be supported later.

### Step 1: Create directory in the repository dedicated for scalability test
Let's assume we created a dedicated directory in repository: `<repo_name>/<bee_scalability_test_dir>`

### Step 2: Create `beefile`
* Inside `<repo_name>/<bee_scalability_test_dir>`, create a beefile named as `<application_name>.beefile`. 
* Follow the instruction for BEE-OpenStack Luancher to compose the beefile with two differences
	*  In `exec_env_conf`->`bee_os`->`num_of_nodes` section, input the maximum number of nodes needed to complete the whole scalability test.
	*  In 'task_conf'->`mpi_run`, provide a list of parallel run configutations for scalability test. Each of them will be executed during the test.

### Step 4: Add an executable result parser

* For each execution in scalability test, `BeeSwarn` will save its output at 

```<repo_name>/<bee_scalability_test_dir>/bee_scalability_test_<number of nodes>_{processes per node}_.output``` 

* It is the developers' responsibility to create a executable result parser (e.g., Shell script, Python script, etc.) to parse information out of those output files and gather into one single result file with name: 

```<repo_name>/<bee_scalability_test_dir>/bee_scalability_test_result_build_${TRAVIS_BUILD_NUMBER}.csv```

* `${TRAVIS_BUILD_NUMBER}` is a environment variable set by Travis CI and we use that in the filename to avoid files being overwritten between builds.

* Place the result parser also in `<repo_name>/<bee_scalability_test_dir>`.

### Step 5: Setup environment variable in Travis CI

* Depending on the platform chosen some environment variables needs to be set in Travis CI.

* For example, when using Chameleon cloud, we need to set the following environment variables:
	* `OS_AUTH_URL`
	* `OS_TENANT_ID`
	* `OS_TENANT_NAME`
	* `OS_REGION_NAME`
	* `OS_USERNAME`
	* `OS_PASSWORD`

* If using BEE_Private repo, a GitHub personal token also need to be created and set environment variable: `GH_TOKEN`.

* Those environment variables can be set either in `.travis.yml` or Travis CI settings. It is recommand to set environment variables that contains password or tokens in Travis CI settings, since it is automically hidden in Travis CI output.



### Step 6: Configure the `.travis.yml` file
The final step is to modifiy the original `.travis.yml` file to enable scalability test. Since BEE only supports containerized applications, all applications must be in container image format (e.g., Docker container) and upload to container registery (e.g., DockerHub) that can be accessed from scalability test environments. 

Place all scripts in the section `after_success` in order:

*  `- cd ${HOME}`
*  `- git clone https://${GH_TOKEN}@github.com/lanl/BEE_Private.git && cd ./BEE_Private`
*  `- ./install_on_travis.sh`
*  `- export PATH=$(pwd)/bee-launcher:$PATH`
*  `- export PATH=$(pwd)/travis_ci:$PATH`
*  `- export PATH=${HOME}/build/${TRAVIS_REPO_SLUG}/<bee_scalability_test_dir>:$PATH`
*  ` - source ${HOME}/build/${TRAVIS_REPO_SLUG}/<bee_scalability_test_dir>/<open_stack_rc_file>`
*  `- cd ${HOME}/build/${TRAVIS_REPO_SLUG}/<bee_scalability_test_dir>`  
*  `- travis_wait <allocated time> bee_ci_launcher.py -l <app_name> -r $OS_RESERVATION_ID`
*  `- output_parser.py`
*  `- push_results_to_repo.sh`





