## Build and Execute Environment (BEE) User Guide for `BeeSwarm`

The following guide shows you how to run `BeeSwarm` to enable scalability test in Continuous Integration. `BeeSwarm` currently support Travis CI with scalability test on Chameleon cloud. More platforms will be supported later.

### Step 1: Configure the `.travis.yml` file
The first step is to modifiy the original `.travis.yml` file to enable scalability test. Since BEE only supports containerized applications, all application must be in container image format (e.g., Docker container) and upload to container registery (e.g., DockerHub) that can be accessed from scalability test environments. 

Suppose we have a directory in the repository dadicated for scalability test (contains `output_parser` and final results): `<bee_scalability_test_dir>`

Place all scripts in the section `after_success` in order:

*  `- cd ${HOME}`
*  `- git clone https://${GH_TOKEN}@github.com/lanl/BEE_Private.git && cd ./BEE_Private`
*  `- ./install_on_travis.sh`
*  `- export PATH=$(pwd)/bee-launcher:$PATH`
*  `- export PATH=$(pwd)/travis_ci:$PATH`
*  `- export PATH=${HOME}/build/${TRAVIS_REPO_SLUG}/<bee_scalability_test_dir>:$PATH`
*  ` - source ${HOME}/build/${TRAVIS_REPO_SLUG}/<bee_scalability_test_dir>/<open_stack_rc_file>`
*  `- cd ${HOME}/build/${TRAVIS_REPO_SLUG}/<bee_scalability_test_dir>`  
*  `- travis_wait 120 bee_ci_launcher.py -l <app_name> -r $OS_RESERVATION_ID`
*  `- output_parser.py`
*  `- push_results_to_repo.sh`

### Step 2: Configure the `<app_name>.beefile` file


### Step 3: Configure Travis CI

### Step 4: Add customized result parser


