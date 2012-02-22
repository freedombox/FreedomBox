#! /usr/bin/python # -*- fill-column: 80 -*-

"""The Santiago service.

It runs on a port (the Port of Santiago) with sending and receiving services
(the Santiagi) with a simple authentication mechanism ("the Dance of the
Santiagi" or "Santiago's Dance").  The idea is that systems can share
identification information without ever revealing their location (where in the
world is Santiago?).

This *is* signed identity statements, just on a
service-by-service-for-individual-people level.  Granularity, bitches!

hackyhackyhacky hacks, but the right structure sans details (a tracer-bullet
structure, see "The Pragmatic Programmer", Hunt & Thomas, 2000, pg. 48).  If
you have a copy of TPP around, also see pgs: 111 120 161 186 192 238 248 258.

This file is distributed under the GPL, version 3 or later, at your discretion.

                                  Santiago, he
                          smiles like a Buddah, 'neath
                               his red sombrero.

"""

# If you're crazy like me, you can turn this script into its own
# documentation by running::
#
#     python pylit.py -c backup - | rst2html > backup.html
#
# You'll need PyLit_ and ReStructuredText_ for this to work correctly.
#
# .. _pylit: http://pylit.berlios.de/
# .. _restructuredtext: http://docutils.sourceforge.net/rst.html
#
# .. contents::

import cherrypy
import os
from simplejson import JSONEncoder


DEBUG = 0
encoder = JSONEncoder()


if DEBUG:
    for x in range(0, 3):
        for y in range(0, 7):
            print "WARNING",
        print ""
    print "You're in DEBUG MODE!  You are surprisingly vulnerable!  Raar!"

def fix_old_cherrypy():
    """Make Lenny's CherryPy forward-compatible."""

    for x in range(0,3):
        for y in range(0, 7):
            print "WARNING",
        print ""

    print("You're using an old CherryPy version!  We're faking it!")
    print("Expect the unexpected!  Raar!")

    def jsonify_tool_callback(*args, **kwargs):
        response = cherrypy.response
        response.headers['Content-Type'] = 'application/json'
        response.body = encoder.iterencode(response.body)

    cherrypy.tools.json_out = cherrypy.Tool('before_finalize', jsonify_tool_callback, priority=30)

if cherrypy.__version__ < "3.2":
    fix_old_cherrypy()


class Santiago(object):
    """Santiago's base class, containing listener and sender defaults."""

    DEFAULT_RESPONSE = """\
<html><head><title>Use it right.</title></head><body>

    <p>Nice try, now try again with a request like:</p>
    <p>http://localhost:8080/santiago/(gpgId)/(service)/(server)</p>

    <dl>
        <dt>gpgId</dt><dd>james, ian</dd>
        <dt>service</dt><dd>wiki, web</dd>
        <dt>server</dt><dd>nick</dd>
    </dl>

    <p>This'll get you good results:</p>
    <code><a href="http://localhost:8080/santiago/james/wiki/nick">
        http://localhost:8080/santiago/james/wiki/nick</a></code>

    <p>See the <code>serving_to</code>, <code>serving_what</code>, and
    <code>me</code> variables.</p>

</body></html>"""

    def __init__(self, instance):
        self.load_instance(instance)

        # TODO Does the listener need to know what services others are running?
        # TODO Does the sender need to know what services I'm running?
        self.load_serving_to()
        self.load_serving_what()
        self.load_known_services()

    def am_i(self, server):
        return str(self.me) == str(server)

    def load_instance(self, instance):
        """Load instance settings from a file.

        A terrible, unforgivable hack.  But it's a pretty effective prototype,
        allowing us to add and remove attributes really easily.

        """
        settings = run_file("%s%ssettings.py" % (instance, os.sep))
        for key, value in settings.iteritems():
            setattr(self, key, value)

        self.instance = instance

    # FIXME I need to handle instance vs controller correctly.  this is the
    # wrong place.
    #
    # I'm putting instance data into the controller, which is nutters.  Too
    # tired to fix tonight, though.
    #
    # These data should probably be loaded in the server and listener,
    # respectively, but I don't know whether one needs to know about the other's
    # services.

    def load_serving_to(self):
        """Who can see which of my services?"""

        self.serving_to = run_file("%s%sserving_to.py" % (self.instance,
                                                          os.sep))
    def load_serving_what(self):
        """What location does that service translate to?"""

        self.serving_what = run_file("%s%sserving_what.py" % (self.instance,
                                                              os.sep))
    def load_known_services(self):
        """What services do I know of?"""

        self.known_services = run_file("%s%sknown_services.py" % (self.instance,
                                                                  os.sep))
    @cherrypy.expose
    def index(self):
        """Do nothing, unless we're debugging."""

        if DEBUG:
            return DEFAULT_RESPONSE


class SantiagoListener(Santiago):
    """Listens for requests on the santiago port."""

    def __init__(self, instance, port=8080):
        super(SantiagoListener, self).__init__(instance=instance)

        self.socket_port = port

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def santiago(self, from_id=None, to_id=None, service=None, hops=0): #, new_santiago_id=""):
        """Handles an incoming request.

        FIXME: handle new Santiago ID list.

        """
        message = { "requester": from_id,
                    "server": to_id,
                    "service": service,
                    "hops": hops, }
                    #"santiago": new_santiago_id }

        # FIXME: this is being dumb and not working how I expect it.  later.
        # if not self.i_am(message["server"]):
        #     return self.proxy_santiago_request(message)

        try:
            return self.serving_what[
                self.serving_to[message["requester"]][message["service"]]]
        except KeyError:
            # TODO: handle responses.  should a fail just timeout?
            return None

    @cherrypy.tools.json_out()
    def proxy_santiago_request(self, message, hops=3):
        """Passes a Santiago request off to another known host.

        We're trying to search the friend list for the target server.

        """
        # handle crap input.
        if (hops > self.max_hops):
            hops = self.max_hops
        if (hops < 1):
            return

        # this counts as a hop.
        hops -= 1

        # TODO pull this off, another day.
        return str(message)


class SantiagoSender(Santiago):
    """Sendss the Santiago request to a Santiago service."""
    
    def __init__(self, instance, proxy):
        super(SantiagoSender, self).__init__(instance=instance)

        self.proxy = proxy if proxy in self.proxy_list else None

    def request(self, destination, resource):
        """Sends a request for a resource to a known Santiago.

        The request MUST include the following:

        - A service.
        - A server.

        The request MAY include the following:

        - Other Santiago listeners.
        - An action.

        post:
            not (__return__["destination"] is None)
            not (__return__["service"] is None)
            # TODO my request is signed with my GPG key, recipient encrypted.

        """
        pass # TODO: do.


# utility functions
# =================

def run_file(filename):
    """Returns the result of executing the Python file.  Terrible idea.  Effective
    hack.

    TODO: Replace this with James's database stuff!

    If you try to use this in the wild, I will hunt you down and cut you.

    """
    with open(filename) as in_file:
        return eval("".join(in_file.readlines()))


if __name__ == "__main__":
    santiago = SantiagoListener("fbx")

    cherrypy.quickstart(santiago)
