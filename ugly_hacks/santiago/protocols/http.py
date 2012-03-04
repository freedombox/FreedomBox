import cherrypy
import santiago
from simplejson import JSONEncoder

encoder = JSONEncoder()


# dirty hacks for Debian Squeeze (stable)
# =======================================

def fix_old_cherrypy():
    """Make Squeeze's CherryPy forward-compatible."""

    for y in range(0,3):
        for x in range(0, 7):
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


# actual HTTP Santiago classes.
# =============================

class SantiagoHttpListener(santiago.SantiagoListener):
    """Listens for connections on the HTTP protocol."""

    DEFAULT_RESPONSE = """\
<html><head><title>Use it right.</title></head><body>

    <p>Nice try, now try again with a request like:</p>
    <p>http://localhost:8080/santiago/(requester)/(server)/(service)</p>

    <dl>
        <dt>requster</dt><dd>james, ian</dd>
        <dt>server</dt><dd>nick</dd>
        <dt>service</dt><dd>wiki, web</dd>
    </dl>

    <p>This'll get you good results:</p>
    <code><a href="http://localhost:8080/santiago/james/nick/wiki">
        http://localhost:8080/santiago/james/nick/wiki</a></code>

    <p>See the <code>serving_to</code>, <code>serving_what</code>, and
    <code>me</code> variables.</p>

</body></html>"""

    def __init__(self, instance, port=8080):
        super(SantiagoHttpListener, self).__init__(instance)
        self.socket_port = port

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def serve(self, key=None, service=None, server=None, hops=3, santiagi=None):
        """Handles an incoming request."""

        return super(SantiagoHttpListener, self).serve(
            key, service, server, hops, santiagi)

    @cherrypy.expose
    def index(self):
        """Do nothing, unless we're debugging."""

        if santiago.DEBUG:
            return self.DEFAULT_RESPONSE


class SantiagoHttpSender(santiago.SantiagoSender):
    """Responsible for answering HTTP requests."""

    @cherrypy.tools.json_out()
    def proxy(self, key, service, server, hops=3):
        """Forwards on a request to another Santiago."""

        return super(SantiagoHttpSender, self).proxy(key, service, server, hops)
