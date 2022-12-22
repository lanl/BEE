Publishing a new release
************************

1. Change the version in pyproject.toml and verify docs build;
   and get this change merged into develop.

2. On github site go to Settings; on the left under Code and Automation
   click on Branches; under Branch protection rules edit main;
    check Allow specified actors to bypass required pull requests; add yourself
    and don'forget to save the setting
3. Checkout main and merge develop into main. Make sure documentation will be 
   published upon push to main (.github/workflows/docs.yml) and push.
4. Once merged, create a tag
   with something like ``git tag -a 0.1.1 -m "BEE version 0.1.1"``. You can see
   existing tags with ``git tag``. Finally do ``git push origin --tags`` to
   push the new tag.
5. Create release.
6. Follow step 2 but uncheck Allow specified actors to bypass and don't forget save
7. Finally, on the main branch, first run a ``poetry build`` and then a
   ``poetry publish``. The second command will ask for a username and password
   for PyPI.

**WARNING**: Once a version is pushed to PyPI, it cannot be undone. You can
'delete' the version from the package settings, but you can no longer publish
an update to that same version.
