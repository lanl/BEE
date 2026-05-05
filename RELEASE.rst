Publishing a new release
************************

Verify all current changes in develop run correctly on nightly tests.
** This may not work unless on site esp. the PYPI portion **

Note: If you are publishing a pre-release from develop just checkout develop and pull,
verify it is up to date and do steps 7 & 8 but stay on the develop branch. For both
pre-releases (that will be published on PYPI) and release versions verify the information in
README.rst has the correct tags and URL's.

1. Start a branch from the current develop branch (pull if needed), named Release-0.x.x
    - change the version in pyproject.toml and README.rst
    - verify docs build
    - add to HISTORY.md for this release.
    - merge the release branch into develop. (You may want to set the bypass as in step 2 on develop).

2. On github site go to Settings; on the left under Code and Automation
   click on Branches; under Branch protection rules edit main;
    check Allow specified actors to bypass required pull requests; add yourself
    and don't forget to save the setting
3. Make sure documentation will be published upon push to main.
   See: .github/workflows/docs.yml
4. Checkout develop and pull for latest version then
   checkout main, pull  and merge develop into main. Verify documentation was published. And re-sync develop. **This procedure assumes you have exceptions and should probably be rewritten to include pull requests.**

.. code-block:: bash

    git checkout develop
    git pull origin develop
    git checkout main
    git pull origin main
    git merge --no-ff develop
    git push origin main

.. code-block:: bash

    git checkout develop
    git merge main
    git push origin develop


5. Once merged, on github web interface create a release and tag based on main branch.
   that matches the version in pyproject.toml
6. Log into your PYPI account and get a token for hpc-beeflow via:

        > Your projects > hpc-beeflow > Manage > Settings > Create a token

7. Finally, on the command line: checkout the main branch and make sure you pull the latest verison

   Then publish by:
       ``poetry build``

       ``poetry publish -u __token__ -p pypi-<long-token>``


Check the documentation at: `https://lanl.github.io/BEE/ <https://lanl.github.io/BEE/>`_ 

Also upgrade the pip version in your python or anaconda environment and check the version:

 `` pip install --upgrade pip``

 `` pip install hpc-beeflow==0.1.x``

**WARNING**: Once a version is pushed to PyPI, it cannot be undone. You can
'delete' the version from the package settings, but you can no longer publish
an update to that same version.

8. After the RELEASE (e.g. 0.1.11) is published:

   Create and merge PR into develop to include:
     - change the version in pyproject.toml to be 0.1.12dev (use latest +1)

   Consider starting a pre-release tag so documentation is updated
   and delete previous pre-release tag's



9. Last but not least, get rid of  exceptions on github. Follow step 2 but uncheck Allow specified actors to bypass for both main and develop, and don't forget save.

