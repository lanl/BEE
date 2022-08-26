#!/bin/sh
# It seems that pytest attempts to import all tests at once, which is a problem
# since this messes with beeflow's configuration mechanism. This basically runs
# pytest on each test one after the other to avoid this, as well as ignoring
# certain tests.

set +e
CODE=0
FAILED=""
IGNORE="test_scheduler_rest.py test_tm.py test_wf_interface.py test_wf_manager.py test_parser.py test_slurm_worker.py"
PASS=0
COUNT=0

# Check if a test should be ignored
function ignore() {
    for other_test in $IGNORE; do
        if [ "$other_test" = "`basename $test`" ]; then
            return 0
        fi
    done
    return 1
}

for test in beeflow/tests/test_*.py; do
    # Check if this is to be ignored
    if ignore $test; then
        continue
    fi
    pytest $test
    result=$?
    if [ $result -ne 0 ]; then
        CODE=$result
        FAILED=$FAILED" $test"
    else
        PASS=`expr $PASS + 1`
    fi
    COUNT=`expr $COUNT + 1`
done

printf "############################# UNIT TEST RESULTS ##############################\n"
printf "$COUNT test(s) ran, $PASS test(s) passed, `expr $COUNT - $PASS` test(s) failed\n"
if [ $CODE -ne 0 ]; then
    printf "The following tests failed:\n"
    for test in $FAILED; do
        printf "    * $test\n"
    done
fi
exit $CODE
