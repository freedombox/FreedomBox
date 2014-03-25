import os, cherrypy
from gettext import gettext as _
from auth import require
from plugin_mount import PagePlugin
import actions
import cfg

class diagnostics(PagePlugin):
    order = 30
    def __init__(self, *args, **kwargs):
        PagePlugin.__init__(self, *args, **kwargs)
        self.register_page("sys.diagnostics")
        cfg.html_root.sys.menu.add_item("Diagnostics", "icon-screenshot", "/sys/diagnostics", 30)

    @cherrypy.expose
    @require()
    def index(self):
        main = _("""
        <p>The system diagnostic test will run a number of checks on your
        system to confirm that network services are running and configured
        properly. It may take a minute to complete.</p>
        """)
        main += '<p><a class="btn btn-primary btn-large" href="'+cfg.server_dir+'/sys/diagnostics/test">Run diagnostic test &raquo;</a></p>'
        return self.fill_template(title=_("System Diagnostics"), main=main)

class test(PagePlugin):
    order = 31
    def __init__(self, *args, **kwargs):
        PagePlugin.__init__(self, *args, **kwargs)
        self.register_page("sys.diagnostics.test")

    @cherrypy.expose
    @require()
    def index(self):
        main = ''
        output, error = actions.superuser_run("diagnostic-test")

        if error:
            main += _("The diagnostic test encountered an error:</br>")
            for line in error.split('\n'):
                main += line + "</br>"

        if output:
            main += _("Output of diagnostic test:</br>")
            for line in output.split('\n'):
                main += line + "</br>"

        return self.fill_template(title=_("Diagnostic Test"), main=main)
