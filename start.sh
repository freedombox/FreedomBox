#! /bin/sh

#PYTHONPATH=vendor/exmachina:$PYTHONPATH

export PYTHONPATH

sudo killall exmachina.py
sudo vendor/exmachina/exmachina.py -v &
python plinth.py
sudo killall exmachina.py
