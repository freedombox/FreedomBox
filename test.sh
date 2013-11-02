#! /bin/sh

# This file is meant to be run from the Plinth root directory:
#
# $ cd plinth/
# $ ./test.sh

PYTHONPATH=modules/installed/lib:$PYTHONPATH
PYTHONPATH=vendor:$PYTHONPATH
PYTHONPATH=.:$PYTHONPATH
export PYTHONPATH

for arg in "$@"
do
    if [ "$arg" = "--pause" ]
    then
        pause=1
    fi
done

for file in tests/*.py
do
    echo "Testing ${file}:"
    python $file

    if [ "$pause" = 1 ]
    then
        read X
    fi
done
