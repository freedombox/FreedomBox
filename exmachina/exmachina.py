#!/usr/bin/env python

"""
Author: bnewbold <bnewbold@robocracy.org>
Date: July 2012
License: GPLv3 (see http://www.gnu.org/licenses/gpl-3.0.html)
         (two helper functions copied from web, as cited below)
Package Requirements: python-augeas, bjsonrpc

This file implements both ends (privilaged daemon and unprivilaged python
client library) of a crude system configuration message bus, intended for use
(initially) with the Plinth web interface to the FreedomBox operating system.

The goal is to provide partially-untrusted processes (such as the web interface
running as the www-data user) access to core system configuration files
(through the Augeas library) and daemon control (through the init.d scripts).

The daemon process (started in the same startup script as Plinth) runs as root
and accepts JSON-RPC method calls through a unix domain socket
(/tmp/exmachina.sock by default). Because file access control may not be
sufficiently flexible for access control, a somewhat-elaborate secret key
mechanism can be used to control access to the RPC mechanism.

The (optional) shared secret-key mechanism requires clients to first call the
"authenticate" RPC method before any other methods. The secret key is passed to
the server process through stdin at startup (command line arguments could be
snooped by unprivilaged processes), and would presumably be passed on to the
client in the same way. The init_test.sh script demonstrates this mechanism.
"""

import os
import sys
import grp
import shutil
import argparse
import logging
import socket
import subprocess
import time
import base64

import bjsonrpc
import bjsonrpc.handlers
import bjsonrpc.server
import augeas

log = logging.getLogger(__name__)


def execute_service(servicename, action, timeout=10):
    """This function mostly ripped from StackOverflow:
    http://stackoverflow.com/questions/1556348/python-run-a-process-with-timeout-and-capture-stdout-stderr-and-exit-status
    """
    # ensure service name isn't tricky trick
    script = "/etc/init.d/" + os.path.split(servicename)[1]

    if not os.path.exists(script):
        raise ValueError("so such service: %s" % servicename)

    command_list = [script, action]
    log.info("executing: %s" % command_list)
    proc = subprocess.Popen(command_list,
                            bufsize=0,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    poll_seconds = .250
    deadline = time.time() + timeout
    while time.time() < deadline and proc.poll() is None:
        time.sleep(poll_seconds)

    if proc.poll() is None:
        if float(sys.version[:3]) >= 2.6:
            proc.terminate()
        raise Exception("execution timed out (>%d seconds): %s" %
                        (timeout, command_list))

    stdout, stderr = proc.communicate()
    # TODO: should raise exception here if proc.returncode != 0?
    return stdout, stderr, proc.returncode

def execute_apt(packagename, action, timeout=120, aptargs=['-q', '-y']):
    # ensure package name isn't tricky trick
    if action != "update" \
            and (packagename != packagename.strip().split()[0] \
                 or packagename.startswith('-')):
        raise ValueError("Not a good apt package name: %s" % packagename)

    if action == "update":
        command_list = ['apt-get', action]
    else:
        command_list = ['apt-get', action, packagename]
    command_list.extend(aptargs)
    log.info("executing: %s" % command_list)
    proc = subprocess.Popen(command_list,
                            bufsize=0,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    poll_seconds = .250
    deadline = time.time() + timeout
    while time.time() < deadline and proc.poll() is None:
        time.sleep(poll_seconds)

    if proc.poll() is None:
        if float(sys.version[:3]) >= 2.6:
            proc.terminate()
        raise Exception("execution timed out (>%d seconds): %s" %
                        (timeout, command_list))

    stdout, stderr = proc.communicate()
    return stdout, stderr, proc.returncode


class ExMachinaHandler(bjsonrpc.handlers.BaseHandler):

    # authentication state variable. If not None, still need to authenticate;
    # if None then authentication not require or was already successful for
    # this instantiation of the Handler.  This class variable gets optionally
    # overridden on a per-process basis
    secret_key = None

    def _setup(self):
        self.augeas = augeas.Augeas()

    def authenticate(self, secret_key):
        if not self.secret_key:
            log.warn("Unecessary authentication attempt")
            return
        if not secret_key.strip() == self.secret_key.strip():
            # fail hard
            log.error("Authentication failed!")
            sys.exit()
        self.secret_key = None

    # ------------- Augeas API Passthrough -----------------
    def augeas_save(self):
        if not self.secret_key:
            log.info("augeas: saving config")
            return self.augeas.save()

    def augeas_set(self, path, value):
        if not self.secret_key:
            log.info("augeas: set %s=%s" % (path, value))
            return self.augeas.set(path.encode('utf-8'),
                                value.encode('utf-8'))

    def augeas_setm(self, base, sub, value):
        if not self.secret_key:
            log.info("augeas: setm %s %s = %s" % (base, sub, value))
            return self.augeas.setm(base.encode('utf-8'),
                                    sub.encode('utf-8'),
                                    value.encode('utf-8'))

    def augeas_get(self, path):
        if not self.secret_key:
            # reduce verbosity
            log.debug("augeas: get %s" % path)
            return self.augeas.get(path.encode('utf-8'))

    def augeas_match(self, path):
        if not self.secret_key:
            # reduce verbosity
            log.debug("augeas: match %s" % path)
            return self.augeas.match("%s" % path.encode('utf-8'))

    def augeas_insert(self, path, label, before=True):
        if not self.secret_key:
            log.info("augeas: insert %s=%s" % (path, value))
            return self.augeas.insert(path.encode('utf-8'),
                                    label.encode('utf-8'),
                                    before=before)

    def augeas_move(self, src, dst):
        if not self.secret_key:
            log.info("augeas: move %s -> %s" % (src, dst))
            return self.augeas.move(src.encode('utf-8'), dst.encode('utf-8'))

    def augeas_remove(self, path):
        if not self.secret_key:
            log.info("augeas: remove %s" % path)
            return self.augeas.remove(path.encode('utf-8'))

    # ------------- Misc. non-Augeas Helpers -----------------
    def set_timezone(self, tzname):
        if not self.secret_key:
            log.info("reset timezone to %s" % tzname)
            tzname = tzname.strip()
            tzpath = os.path.join("/usr/share/zoneinfo", tzname)
            try:
                os.stat(tzpath)
            except OSError:
                # file not found
                raise ValueError("timezone not valid: %s" % tzname)
            shutil.copy(
                os.path.join("/usr/share/zoneinfo", tzname),
                "/etc/localtime")
            with open("/etc/timezone", "w") as tzfile:
                tzfile.write(tzname + "\n")
            return "timezone changed to %s" % tzname

    # ------------- init.d Service Control -----------------
    def initd_status(self, servicename):
        if not self.secret_key:
            return execute_service(servicename, "status")

    def initd_start(self, servicename):
        if not self.secret_key:
            return execute_service(servicename, "start")

    def initd_stop(self, servicename):
        if not self.secret_key:
            return execute_service(servicename, "stop")

    def initd_restart(self, servicename):
        if not self.secret_key:
            return execute_service(servicename, "restart")

    # ------------- apt-get Package Control -----------------
    def apt_install(self, packagename):
        if not self.secret_key:
            return execute_apt(packagename, "install")

    def apt_update(self):
        if not self.secret_key:
            return execute_apt("", "update")

    def apt_remove(self, packagename):
        if not self.secret_key:
            return execute_apt(packagename, "remove")


class EmptyClass():
    # Used by ExMachinaClient below
    pass


class ExMachinaClient():
    """Simple client wrapper library to expose augeas and init.d methods.

    In brief, use augeas.get/set/insert to modify system configuration files
    under the /files/etc/* namespace. augeas.match with a wildcard can be used
    to find variables to edit.

    After making any changes, use augeas.save to commit to disk, then
    initd.restart to restart the appropriate system daemons. In many cases,
    this would be the 'networking' meta-daemon.

    See test_exmachina.py for some simple examples; see the augeas docs for
    more in depth guidance.
    """

    def __init__(self,
                 socket_path="/tmp/exmachina.sock",
                 secret_key=None):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(socket_path)
        self.conn = bjsonrpc.connection.Connection(self.sock)

        if secret_key:
            self.conn.call.authenticate(secret_key)

        self.augeas = EmptyClass()
        self.initd = EmptyClass()
        self.apt = EmptyClass()
        self.misc = EmptyClass()

        self.augeas.save = self.conn.call.augeas_save
        self.augeas.set = self.conn.call.augeas_set
        self.augeas.setm = self.conn.call.augeas_setm
        self.augeas.get = self.conn.call.augeas_get
        self.augeas.match = self.conn.call.augeas_match
        self.augeas.insert = self.conn.call.augeas_insert
        self.augeas.move = self.conn.call.augeas_move
        self.augeas.remove = self.conn.call.augeas_remove
        self.initd.status = self.conn.call.initd_status
        self.initd.start = self.conn.call.initd_start
        self.initd.stop = self.conn.call.initd_stop
        self.initd.restart = self.conn.call.initd_restart
        self.apt.install = self.conn.call.apt_install
        self.apt.update = self.conn.call.apt_update
        self.apt.remove = self.conn.call.apt_remove
        self.misc.set_timezone = self.conn.call.set_timezone

    def close(self):
        self.sock.close()


def run_server(socket_path, secret_key=None, socket_group=None):

    if not 0 == os.geteuid():
        log.warn("Expected to be running as root!")

    if os.path.exists(socket_path):
        os.unlink(socket_path)
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.bind(socket_path)
    sock.listen(1)

    if socket_group is not None:
        socket_uid = os.stat(socket_path).st_uid
        socket_gid = grp.getgrnam(socket_group).gr_gid
        os.chmod(socket_path, 0660)
        os.chown(socket_path, socket_uid, socket_gid)
    else:
        os.chmod(socket_path, 0666)
    if secret_key:
        ExMachinaHandler.secret_key = secret_key

    serv = bjsonrpc.server.Server(sock, handler_factory=ExMachinaHandler)
    serv.serve()

def daemonize(stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
    """
    From: http://www.noah.org/wiki/Daemonize_Python

    This forks the current process into a daemon. The stdin, stdout, and
    stderr arguments are file names that will be opened and be used to replace
    the standard file descriptors in sys.stdin, sys.stdout, and sys.stderr.
    These arguments are optional and default to /dev/null. Note that stderr is
    opened unbuffered, so if it shares a file with stdout then interleaved
    output may not appear in the order that you expect. """

    # Do first fork.
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)   # Exit first parent.
    except OSError, e:
        sys.stderr.write("fork #1 failed: (%d) %s\n" % (e.errno, e.strerror))
        sys.exit(1)

    # Decouple from parent environment.
    os.chdir("/")
    os.umask(0)
    os.setsid()

    # Do second fork.
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)   # Exit second parent.
    except OSError, e:
        sys.stderr.write("fork #2 failed: (%d) %s\n" % (e.errno, e.strerror))
        sys.exit(1)

    # Now I am a daemon!

    # Redirect standard file descriptors.
    si = open(stdin, 'r')
    so = open(stdout, 'a+')
    se = open(stderr, 'a+', 0)
    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())
    return pid

# =============================================================================
# Command line handling
def main():

    global log
    parser = argparse.ArgumentParser(usage=
        "usage: %prog [options]\n"
        "%prog --help for more info."
    )
    parser.add_argument("-v", "--verbose",
        default=False,
        help="Show more debugging statements",
        action="store_true")
    parser.add_argument("-q", "--quiet",
        default=False,
        help="Show fewer informational statements",
        action="store_true")
    parser.add_argument("-k", "--key",
        default=False,
        help="Wait for Secret Access Key on stdin before starting",
        action="store_true")
    parser.add_argument("--random-key",
        default=False,
        help="Just dump a random base64 key and exit",
        action="store_true")
    parser.add_argument("-s", "--socket-path",
        default="/tmp/exmachina.sock",
        help="UNIX Domain socket file path to listen on",
        metavar="FILE")
    parser.add_argument("--pidfile",
        default=None,
        help="Daemonize and write pid to this file",
        metavar="FILE")
    parser.add_argument("-g", "--group",
        default=None,
        help="chgrp socket file to this group and set 0660 permissions")

    args = parser.parse_args()

    #if len(args) != 0:
        #parser.error("Incorrect number of arguments")

    if args.random_key:
        sys.stdout.write(base64.urlsafe_b64encode(os.urandom(128)))
        sys.exit(0)

    log = logging.getLogger()
    hdlr = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    log.addHandler(hdlr)

    if args.verbose:
        log.setLevel(logging.DEBUG)
    elif args.quiet:
        log.setLevel(logging.ERROR)
    else:
        log.setLevel(logging.INFO)

    secret_key = None
    if args.key:
        log.debug("Waiting for secret key on stdin...")
        secret_key = sys.stdin.readline().strip()
        log.debug("Got it!")

    if args.pidfile:
        with open(args.pidfile, 'w') as pfile:
            # ensure file is available/writable
            pass
        os.unlink(args.pidfile)
        daemonize()
        pid = os.getpid()
        with open(args.pidfile, 'w') as pfile:
            pfile.write("%s" % pid)
        log.info("Daemonized, pid is %s" % pid)

    run_server(secret_key=secret_key,
               socket_path=args.socket_path,
               socket_group=args.group)

if __name__ == '__main__':
    main()
