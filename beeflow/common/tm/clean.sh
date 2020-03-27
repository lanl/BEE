#! /bin/bash

read -p 'Do you want to remove submitted scripts ~/.beeflow/worker/workflow-* (y/n)?' ans 
if [ $ans == 'y' ] || [ $ans == 'Y' ] 
then
  echo 'Removing scripts!'
  rm -rf ~/.beeflow/worker/workflow-*
else
  echo 'Did not remove scripts.'
fi
rm *.log
rm *.out
rm *.json
