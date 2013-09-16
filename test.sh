#! /bin/sh

PYTHONPATH=modules/installed/lib:$PYTHONPATH
PYTHONPATH=vendor:$PYTHONPATH

export PYTHONPATH

python tests/test_user_store.py
