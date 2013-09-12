#!/usr/bin/env bash

# Test init.d-style initialization; run this script as root (or sudo it)

export key=`./exmachina.py --random-key`

echo $key | ./exmachina.py -vk --pidfile /tmp/exmachina_test.pid -g www-data
sleep 1
echo $key | sudo -u www-data -g www-data ./test_exmachina.py -k

kill `cat /tmp/exmachina_test.pid` && rm /tmp/exmachina_test.pid
sleep 1
jobs
