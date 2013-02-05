#! /bin/sh

PYTHONPATH=build/exmachina:$PYTHONPATH

export PYTHONPATH

sudo killall exmachina.py
sudo build/exmachina/exmachina.py -v &
python plinth.py
sudo killall exmachina.py
