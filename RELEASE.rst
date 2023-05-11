Publishing a new release
************************

1. Change the version in pyproject.toml and verify docs build;
   and get this change merged into develop. (You may want to set the bypass as in step 2)
2. On github site go to Settings; on the left under Code and Automation
   click on Branches; under Branch protection rules edit main;
    check Allow specified actors to bypass required pull requests; add yourself
    and don't forget to save the setting
3  Make sure documentation will be published upon push to main.
   See: .github/workflows/docs.yml
4. Checkout develop and pull for latest version then
   checkout main and merge develop into main. Verify documentation was published.
   See actions and site below.
5. Once merged, on github web interface create a release and tag based on main branch
   that matches the version in pyproject.toml
6. Follow step 2 but uncheck Allow specified actors to bypass and don't forget save
7. Finally, on the main branch, first run a ``poetry build`` and then a
   ``poetry publish``. The second command will ask for a username and password
   for PyPI.

Check the documentation at: `https://lanl.github.io/BEE/ <https://lanl.github.io/BEE/>`_ 
Also upgrade the pip version in your python or anaconda environment and check the version:
 `` pip install --upgrade hpc-beeflow``

**WARNING**: Once a version is pushed to PyPI, it cannot be undone. You can
'delete' the version from the package settings, but you can no longer publish
an update to that same version.
