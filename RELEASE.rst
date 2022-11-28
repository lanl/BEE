Publishing a new release
************************

1. Change the version in pyproject.toml and get this change merged into develop.
2. Make another PR to get this merged from develop into main.
3. Once approved and merged, check out the updated main branch and create a tag
   with something like ``git tag -a 0.1.1 -m "BEE version 0.1.1"``. You can see
   existing tags with ``git tag``. Finally do ``git push origin --tags`` to
   push the new tag.
4. Finally, on the main branch, first run a ``poetry build`` and then a
   ``poetry publish``. The second command will ask for a username and password
   for PyPI.

**WARNING**: Once a version is pushed to PyPI, it cannot be undone. You can
'delete' the version from the package settings, but you can no longer publish
an update to that same version.
