Publishing a new release
========================

This procedure covers both final releases and prereleases of BEE. Complete the
release from a system that can run the required LANL tests and reach PyPI. Some
steps may require access to the LANL network.

Before you begin
----------------

* Confirm that the nightly tests for the current ``develop`` branch pass.
* Confirm that the version has not already been published on PyPI. PyPI does
  not allow a version number to be reused, even if that release is deleted.
* Verify that the version, tag names, and documentation URLs in ``README.rst``
  are correct.
* Keep the branch-protection rules for ``main`` and ``develop`` enabled. Use
  pull requests for the release merges.

Publishing a final release
--------------------------

The examples below use ``0.x.x`` as the release version.

1. Update your local ``develop`` branch and create a release branch::

      git switch develop
      git pull --ff-only origin develop
      git switch -c release/0.x.x

2. Prepare the release branch:

   * Set the release version in ``pyproject.toml``.
   * Update the version, tag names, and documentation URLs in ``README.rst``
   * Review the changes since the previous release tag before updating
     ``HISTORY.md``. First, list the tags to identify the previous final
     release::

         git fetch origin --tags
         git tag --sort=-version:refname

     Then review the commits in chronological order, including their full
     messages and changed-file summaries::

         git log <previous-release-tag>..origin/develop --first-parent --reverse --format=fuller --stat

     ``--first-parent`` follows the main ``develop`` history and avoids
     expanding every merged branch into its individual commits. Use the output
     to summarize the user-visible changes in ``HISTORY.md``; do not copy the
     commit messages without reviewing and organizing them.
   * Add the release notes to ``HISTORY.md``.
   * Check and commit changes to pyproject.toml, README.rst History.md
   * Build the documentation and review the generated output.
   * Run the applicable tests.

3. Push the branch and create a pull request into ``develop``::

      git push -u origin release/0.x.x

   Create PR.
   Merge the pull request only after its required checks and review are
   complete.

4. Create a pull request from ``develop`` into ``main``. Confirm that the pull
   request contains only the changes intended for this release, then merge it
   after all required checks and review are complete.

5. Verify the release commit on ``main``:

   * The version in ``pyproject.toml`` matches the planned release version.
   * The documentation workflow in ``.github/workflows/docs.yml`` completed
     successfully.

   * The current coverage badge is available at:   
       | https://lanl.github.io/BEE/badges/develop/coverage.svg     
       | https://lanl.github.io/BEE/badges/main/coverage.svg
  
6. On GitHub, create a release from the release commit on ``main``. Create a
   tag whose version matches ``pyproject.toml`` exactly, and publish the GitHub
   release.

   After github actions have run, verify the documentation:
   | https://lanl.github.io/BEE/

7. Check out the tagged release and build the distributions::

      git fetch --tags origin
      git switch --detach <release-tag>
      poetry build

   Inspect the files in ``dist/`` before publishing. If the version or package
   contents are wrong, fix them before continuing.

8. Create a project-scoped API token for ``hpc-beeflow`` on PyPI:
       | ``Your projects > hpc-beeflow > Manage Projects > Settings > Create a token``.

   poetry publish -u __token__ -p <pypi-long token>


9. Verify the published package in a clean virtual environment (ensure python3 is a good version for beeflow)::

      python3 -m venv /tmp/beeflow-release-check
      . /tmp/beeflow-release-check/bin/activate
      python -m pip install --upgrade pip
      python -m pip install hpc-beeflow==0.x.x
      python -m pip show hpc-beeflow

10. Prepare a branch for ``develop`` for the next development cycle in a new pull request:

    * Change the version in ``pyproject.toml`` to the next development version,
      for example ``0.1.12dev1`` after releasing ``0.1.11``.
    * Update the prerelease version, tag names, and documentation URLs in
      ``README.rst``.
    * Verify the documentation build, then merge the pull request into
      ``develop`` after its checks and review are complete.
    * Get the branch merged to develop through the normal procedure.
    * Create a tag matching ``pyproject.toml`` (it isn't necessary to publish)

11. If ``main`` received any changes that are not already in ``develop``, merge
    them back through a pull request from ``main`` into ``develop``.

Publishing a prerelease
-----------------------

Publish a prerelease from ``develop``; do not merge ``develop`` into ``main``.

1. Confirm that ``develop`` is current and that its nightly tests pass::

      git switch develop
      git pull --ff-only origin develop

2. Verify that ``pyproject.toml`` contains the intended prerelease version and
   that ``README.rst`` contains the matching tag names and documentation URLs.
   Make any required changes through a pull request into ``develop`` before
   continuing.

3. Create a GitHub prerelease whose tag points to the verified commit on
   ``develop`` and matches the version in ``pyproject.toml``.

4. Check out that tag, then follow final-release steps 7 through 9 to build,
   publish, and verify the package. Mark the GitHub release as a prerelease.

Do not delete an older PyPI release in an attempt to reuse its version number;
PyPI will not permit that version to be uploaded again. Remove obsolete
prerelease documentation from ``gh-pages`` only when it is no longer linked or
needed.

Release warning
---------------

Publishing to PyPI is permanent for versioning purposes. A published release
can be removed from the project page, but its version number cannot be reused.
