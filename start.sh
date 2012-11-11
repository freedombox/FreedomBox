#! /bin/sh

PYTHONPATH=../exmachina:$PYTHONPATH

sudo killall exmachina.py
sudo ../exmachina/exmachina.py -v &
python plinth.py
sudo killall exmachina.py
