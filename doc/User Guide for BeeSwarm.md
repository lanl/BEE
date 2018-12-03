## Build and Execute Environment (BEE) User Guide for `BeeSwarm`

The following guide shows you how to use `BeeSwarm` to enable scalability test in Continuous Integration on Travis CI and GitLab CI with scalability test on Chameleon cloud. 

### Step 1: Create directory in the repository dedicated for scalability test
Let's assume we created a dedicated directory in repository: `<repo_name>/<bee_scalability_test_dir>`

### Step 2: Create `beefile`
* Inside `<repo_name>/<bee_scalability_test_dir>`, create a beefile named as `<application_name>.beefile`. 
* Follow the instruction for BEE-OpenStack Luancher to compose the beefile with two differences
	*  In `exec_env_conf`->`bee_os`->`num_of_nodes` section, input the maximum number of nodes needed to complete the whole scalability test.

	*  A section `task_conf`->`scalability_run` is used to specify a group of execution configurations for the scalability test. In this section, we have following keys:
		*  `mode` works together with `node_range` and `proc_range` indicates how `BeeSwarm` generate different execution configurations. `linear`/`exp2`/`exp10` mode will generate configurations with number nodes or processes that increase linearly by one, expoentially by 2, or expoentially by 10. In additional, there is an `independet` mode that allows users to specifiy each configurations manully without automatic generation.
		*  `node_range` and `proc_range`: store two numbers that represent the ranges for the number of nodes and the number of processes. Both ranges are inclusive.
		*  `script`: indicate the run script name for the scalability test. The run script need to be in the same directory as beefile.
		*  `local_port_fwd` and `remote_port_fwd`: indicate the ports for creatings forward or backward SSH tunnels. Leave them blank would disable the creation of SSH tunnels.

### Step 3: Add an executable result parser

* For each execution in scalability test, `BeeSwarn` will save its output at 

```<repo_name>/<bee_scalability_test_dir>/bee_scalability_test_<number of nodes>_{processes per node}_.output``` 

* It is the developers' responsibility to create a executable result parser (e.g., Shell script, Python script, etc.) to parse information out of those output files and gather into one single result file with name: 

If on Travis CI:

```<repo_name>/<bee_scalability_test_dir>/bee_scalability_test_result_build_${TRAVIS_BUILD_NUMBER}.csv```

If on GitLab CI:

```<repo_name>/<bee_scalability_test_dir>/bee_scalability_test_result_build_${CI_COMMIT_SHA}.csv```

* `${TRAVIS_BUILD_NUMBER}` and `${CI_COMMIT_SHA}` are environment variables set by Travis CI and GitLab CI and we use that in the filename to avoid files being overwritten between builds.

* Place the result parser also in `<repo_name>/<bee_scalability_test_dir>`.

### Step 4: Setup environment variable in Travis CI or GitLab CI

* Depending on the platform chosen some environment variables needs to be set in Travis CI or GitLab CI.

* For example, when using Chameleon cloud, we need to set the following environment variables:
	* `OS_AUTH_URL`
	* `OS_TENANT_ID`
	* `OS_TENANT_NAME`
	* `OS_REGION_NAME`
	* `OS_USERNAME`
	* `OS_PASSWORD`
	* `OS_ENDPOINT_TYPE`
	* `OS_IDENTITY_API_VERSION`
	* `OS_REGION_NAME`
	* `OS_RESERVATION_ID`
All variables except the last one can be found on Chameleon (`Project`->`Compute`->`API Access`->`Download OpenStack RC File v2.0`). The lest variable `OS_RESERVATION_ID` can be found once a reservation is created. It can be found under `Reservations`->`Leases`->`<lease name>`->`id`. Make sure the number of machines in the reservation is equal or greater than you need in the scalability test.

* If using BEE_Private repo on GitHub, a GitHub personal token also need to be created and set as an environment variable: `GH_TOKEN`.

* To allow `BeeSwarm` commit and push scalability test results back to the original repository, corresponding repo access token need to be set an environment variable:
	* `GH_TOKEN` for GitHub
	* `GL_TOKEN` for GitLab
	
* Those environment variables can be set either in CI script (i.e., `.travis.yml` for Travis CI and `.gitlab-ci.yml` for GitLab CI) or in environment variable setting provided by CI services (it can be found in `More options`->`Settings`->`Environment Variables` for Travis CI or `settings`->`CI/CD`->`Variables` for GitLab CI). It is recommand to set environment variables that contains password or tokens in the second way, since it can automically hide sensitive information in console output.



### Step 5: Configure the `.travis.yml` file for Travis CI or `.gitlab-ci.yml` for GitLab CI
The final step is to modifiy the original `.travis.yml` or `.gitlab-ci.yml` to enable scalability test. Since BEE only supports containerized applications, all applications must be in container image format (e.g., Docker container) and upload to container registery (e.g., DockerHub) that can be accessed from scalability test environments. 

For Travis CI, place all scripts in the section `after_success` in order. Here we show an example of running scalability test on Flecsale with beefile and run script in `bee_scalability_test` folder in repo.

```
# Setup Git
- git config --global user.email "example@beeswarm.org"
- git config --global user.name "BeeSwarm"
- cd ${HOME}/build/${TRAVIS_REPO_SLUG}
- git checkout ${TRAVIS_BRANCH}
 
# Setup BeeSwarm
- cd ${HOME}
- git clone https://github.com/lanl/BEE.git && cd ./BEE
- ./install_for_ci.sh  
- export PATH=$(pwd)/bee-launcher:$PATH

# Start scalability test
- cd ${HOME}/build/${TRAVIS_REPO_SLUG}/bee_scalability_test
- travis_wait 120 bee_ci_launcher.py -l flecsale -r $OS_RESERVATION_ID

# Parse results
- output_parser.py

# Rename and copy result file
- mv bee_scalability_test_parsed.output ${HOME}/build/${TRAVIS_REPO_SLUG}/bee_scalability_test/bee_scalability_test_result_build_${TRAVIS_BUILD_NUMBER}.csv

# Push results back to repo
- git add bee_scalability_test_result_build_${TRAVIS_BUILD_NUMBER}.csv
- git commit --message "[skip ci]"
- git remote add remote_repo https://${GH_TOKEN}@github.com/${TRAVIS_REPO_SLUG}.git
- git push remote_repo ${TRAVIS_BRANCH} 

```

For GitLab CI, the similar script is as follows:
```

# Setup Git 
- git config --global user.email "example@beeswarm.org"
- git config --global user.name "BeeSwarm"
- git remote add remote_repo https://gitlab-ci-token:$GL_TOKEN@gitlab.com/cjy7117/test.git
- git checkout $CI_COMMIT_REF_NAME

# Setup BeeSwarm
- cd ${HOME}
- git clone https://@github.com/lanl/BEE.git && cd ./BEE
- ./install_for_ci.sh
- export PATH=~/.local/bin:$PATH
- export PATH=$(pwd)/bee-launcher:$PATH
    
# Start scalability test
- cd ${CI_PROJECT_DIR}/bee_scalability_test
- bee_ci_launcher.py -l flecsale -r $OS_RESERVATION_ID
     
# Parse output     
- ./output_parser.py

# Rename and copy result file
- cp bee_scalability_test_parsed.output ${CI_PROJECT_DIR}/bee_scalability_test/bee_scalability_test_result_build_${CI_COMMIT_SHA}.csv

# Push results back to repo
- git add bee_scalability_test_result_build_$CI_COMMIT_SHA.csv
- git commit --message "[skip ci]"
- git push remote_repo $CI_COMMIT_REF_NAME

```