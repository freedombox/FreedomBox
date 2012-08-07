#!/usr/bin/env python

"""
This file tests the "client side" of the exmachina layer.

To use with secret keys, do the following in seperate terminals:

    $ echo "<key>" | sudo ./exmachina.py -vk
    $ echo "<key>" | ./test_exmachina.py -k

To use without, do the following in seperate terminals:

    $ sudo ./exmachina.py -v
    $ ./test_exmachina.py

Use the init_test.sh script to test shared key passing and privilage seperation
at the same time:

    $ sudo ./init_test.sh
"""

import sys
import socket

import bjsonrpc
import bjsonrpc.connection
from bjsonrpc.exceptions import ServerError

from exmachina import ExMachinaClient

# =============================================================================
# Command line handling
def main():

    socket_path = "/tmp/exmachina.sock"
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.connect(socket_path)

    secret_key = None
    if sys.argv[-1] == "-k":
        print "waiting for key on stdin..."
        secret_key = sys.stdin.readline()
        print "sent!"

    print "========= Testing JSON-RPC connection"
    c = bjsonrpc.connection.Connection(sock)
    if secret_key:
        c.call.authenticate(secret_key)
    print "/*: %s" % c.call.augeas_match("/*")
    print "/augeas/*: %s" % c.call.augeas_match("/augeas/*")
    print "/etc/* files:"
    for name in c.call.augeas_match("/files/etc/*"):
        print "\t%s" % name
    print c.call.initd_status("bluetooth")
    print "hostname: %s" % c.call.augeas_get("/files/etc/hostname/*")
    print "localhost: %s" % c.call.augeas_get("/files/etc/hosts/1/canonical")
    sock.close()

    print "========= Testing user client library"
    client = ExMachinaClient(secret_key=secret_key)
    print client.augeas.match("/files/etc/*")
    #print client.initd.restart("bluetooth")
    try:
        print client.initd.status("greentooth")
        print "ERROR: should have failed above!"
    except ServerError:
        print "(got expected error, good!)"
    print "(expect Error on the above line)"
    print client.initd.status("bluetooth")
    print client.apt.install("pkg_which_does_not_exist")
    print client.apt.remove("pkg_which_does_not_exist")
    #print client.apt.update() # can be slow...
    #print client.misc.set_timezone("UTC") # don't clobber system...
    try:
        print client.misc.set_timezone("whoopie") # should be an error
        print "ERROR: should have failed above!"
    except ServerError:
        print "(got expected error, good!)"
    client.close()

if __name__ == '__main__':
    main()
