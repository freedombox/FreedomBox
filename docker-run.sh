#!/bin/bash

cd /plinth
service apache2 restart
source ve/bin/activate
exec plinth --no-daemon
