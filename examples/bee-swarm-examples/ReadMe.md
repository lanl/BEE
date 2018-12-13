## Example - Scalability Test for Flecsale on CI using BeeSwarm
1. Fork you own copies of the example repositories at:
  * GitHub: ```https://github.com/cjy7117/flecsale```
  * GitLab: ```https://gitlab.com/cjy7117/flecsale```
* Link your repository with CI service properly.
* Follow the ```User Guide for BeeSwarm``` to setup:
	*	Chameleon cloud reservations;
	* 	Environment variables on CI services;
	*  Timeout for scalability test command;
	*  If needed, modify ```.beefile``` to try different scalability test modes.
* Create and commmit a dummy file inside the repository or in any other ways to make a commit to trigger a test (aka. job) on CI services.
* You can monitor the test progress in the console provided by CI services.
* After done, the scalability test results are pushed under:
	* GitHub: ```https://github.com/<your copy of repo>/bee_scalability_test```
	* GitHub: ```https://gitlab.com/<your copy of repo>/bee_scalability_test```

The results files should have name like: ```bee_scalability_test_result_build_<BUILD INFO>.csv``` where ```<BUILD INFO>``` is the build number if the repository is on GitHub or the last few letters of commit hash code if the repository is on GitLab.