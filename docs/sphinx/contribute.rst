.. _contribute:

Contribute
************

Git Workflow
============

BEE has two lifetime branches, develop and main. To work on a fix or feature, create a branch from develop. These branches should address an open issue and follow the format **issue#/title** (e.g. 'issue857/mpi-integration-test'). If there isn't an issue for your fix or feature consider making one.

All pull requests (PR's) are made from feature or issue branches and undergo review and testing before they can be merged into develop. Open a **work in progress** PR with label of **'WIP'**. Before submitting the PR for approval, merge develop into your branch and fix any conflicts. Remove the 'WIP' label when the PR is complete and ready for final review. GitHub CI tests must pass before merging into develop.

Upon release, develop will be merged by the team lead into main. Additionally, all changes must pass overnight tests before being merged into main.

Style Guide
===========
BEE is python code and adheres to style guidelines specified in **ruff.toml**, enforced using ruff. Before attempting to commit and push changes, please install our pre-commit githooks by running the following command in project root:

If using `git --version` >= 2.9:
    git config core.hooksPath .githooks

Otherwise:
    cp .githooks/* .git/hooks/

Important Notes:
----------------

* To use the git hooks, you must have your Poetry environment set up and activated, as the hooks rely on the environment to run necessary checks.
* If you wish to skip running the git hook for a specific commit, you can do so by using the following command:

.. code-block::

    SKIP=ruff git commit -m "foo"

* Using these git hooks will ensure your contributions adhere to style guidelines required for contribution. You will need to repeat these steps for every **BEE** repo you clone.
