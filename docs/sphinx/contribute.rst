.. _contribute:

Contribute
************

Git Workflow
============

BEE has two lifetime branches, develop and main. All Pull Requests's (PR's) will be reviewed and tested then merged into develop when tests pass and review is complete.

Upon release develop will be merged by the team lead into main.

Open a **work in progress** PR with label of **'WIP'** and link the PR to an issue using the term **'addresses'** issue #.

Merge develop into your branch and fix conflicts before submitting a PR for approval.

Style Guide
===========
BEE is python code and adheres to style guidelines specified in **setup.cfg**. Before attempting to commit and push changes, please install our pre-commit githooks by running the following command in project root:

If using `git --version` >= 2.9:
    git config core.hooksPath .githooks

Otherwise:
    cp .githooks/* .git/hooks/

Using these git hooks will ensure your contributions adhere to style guidelines required for contribution. You will need to repeat these steps for every `BEE` repo you clone.


