Some suggestions that were in the comments in the PR that may have not been addressed yet:

- Instead of copying all the files into the container, just put them in the workflow directory and they'll be bindmounted in when the workflow runs. This would need to be tested. 

- For the inputs, that's kind of an area I haven't thought through well enough. But I'd recommend defining each input variable right above the first task that uses it. Maybe this should be discussed.


Also there are many thoughts in this discussion that may need to be explored

https://github.com/lanl/BEE/discussions/1118 