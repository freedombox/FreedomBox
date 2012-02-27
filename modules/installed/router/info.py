import cherrypy
from plugin_mount import PagePlugin
from modules.auth import require

class Info(PagePlugin):
    title = 'Info'
    order = 10
    url = 'info'

    def __init__(self, *args, **kwargs):
        self.register_page("router.info")

    @cherrypy.expose
    @require()
    def index(self):
        return self.fill_template(title="Router Information", main="""
<p>Eventually we will display a bunch of info, graphs and logs about the routing functions here.</p>
""")
