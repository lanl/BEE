Publishing a new release
************************

Verify all current changes in develop run correctly on nightly tests.

1. Start a branch named Release-0.x.x  Change the version in pyproject.toml and verify docs build, add to HISTORY.md for this release,
   and get this change merged into develop. (You may want to set the bypass as in step 2 on develop).

2. On github site go to Settings; on the left under Code and Automation
   click on Branches; under Branch protection rules edit main;
    check Allow specified actors to bypass required pull requests; add yourself
    and don't forget to save the setting
3. Make sure documentation will be published upon push to main.
   See: .github/workflows/docs.yml
4. Checkout develop and pull for latest version then
   checkout main and merge develop into main. Verify documentation was published.
   See actions and site below.
5. Once merged, on github web interface create a release and tag based on main branch
   that matches the version in pyproject.toml
6. Follow step 2 but uncheck Allow specified actors to bypass and don't forget save
7. Log into your PYPI account and get a token for hpc-beeflow.
8. Finally, on the command line: checkout the main branch and make sure you pull the latest verison

   Then publish by:
       ``poetry build``

       ``poetry publish -u __token__ -p pypi-<long-token>``


Check the documentation at: `https://lanl.github.io/BEE/ <https://lanl.github.io/BEE/>`_ 
Also upgrade the pip version in your python or anaconda environment and check the version:
 `` pip install --upgrade hpc-beeflow``

**WARNING**: Once a version is pushed to PyPI, it cannot be undone. You can
'delete' the version from the package settings, but you can no longer publish
an update to that same version.

8. After the version is published change the version in develop to a pre-release of the next version 
   (example new version will be 0.1.x edit pyproject.toml version to be 0.1.xrc1
