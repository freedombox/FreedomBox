#! /bin/sh

#PYTHONPATH=vendor/exmachina:$PYTHONPATH

export PYTHONPATH

sudo killall exmachina.py
sudo /usr/share/pyshared/exmachina/exmachina.py -v &
python plinth.py
sudo killall exmachina.py
