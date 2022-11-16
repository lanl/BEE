#!/bin/sh

# Needed to run slurmrestd in CI
export SLURMRESTD_SECURITY=disable_user_check

set +e
failed=""
failed_count=0
total=0
start_time=`date +%s`
for tst in beeflow/tests/test_*.py; do
    printf "--> Running $tst\n"
    pytest $tst
    result=$?
    # Ensure the step fails if one test fails
    if [ $result -ne 0 ]; then
        failed=$tst" "$failed
        failed_count=`expr $failed_count + 1`
    fi
    total=`expr $total + 1`
done
end_time=`date +%s`
printf "################################################\n" >&2
printf "$total test(s) run in `expr $end_time - $start_time`s, $failed_count test(s) failed\n" >&2
if [ $failed_count -gt 0 ]; then
    printf "failed tests:\n" >&2
    for tst in $failed; do
        printf "* $tst\n" >&2
    done
    exit 1
else
    exit 0
fi
