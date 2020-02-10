This branch parses the entire cwl workflow and results in a dictionary, it currently
verifies cwl with a copy of cwl's versions.

Things that need to be considered:

1. The return could easily be changed to a python object instead of a dictionary.
2. We should look at linking to cwl's versions from their repository instead of having a copy.
3. No unit tests, yet. I did not want to spend the time on that until we decide to use this.
4. Need to populate the workflow with the yml file, like is used for cwl-runner. (easy?)
5. Do we want to log the verification of the workflow?


