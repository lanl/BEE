Try this:

assumes this BEE_Private repo is in ~/BEE 
also assumes salad-schema in poetry env, if not pip install works

export CWL_VERSIONS=~/BEE/BEE_Private/beeflow/common/parser/cwl-versions/

cd ~/BEE/BEE_Private/examples/parser-examples
python ~/BEE/BEE_Private/tools/validate-cwl/validate_print_cwl.py -h

Now try:

python ~/BEE/BEE_Private/tools/validate-cwl/validate_print_cwl.py -c echo.cwl -l

cd blast-cc
python ~/BEE/BEE_Private/tools/validate-cwl/validate_print_cwl.py -l -c blast-cc-flow.cwl

python ~/BEE/BEE_Private/tools/validate-cwl/validate_print_cwl.py -l -r -c blast-cc-flow.cwl

