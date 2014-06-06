import os
import cherrypy
from gettext import gettext as _
from plugin_mount import PagePlugin
import cfg
import util


class Help(PagePlugin):
    order = 20 # order of running init in PagePlugins
    def __init__(self, *args, **kwargs):
        PagePlugin.__init__(self, *args, **kwargs)
        self.register_page("help")
        self.menu = cfg.main_menu.add_item(_("Documentation"), "icon-book", "/help", 101)
        self.menu.add_item(_("Where to Get Help"), "icon-search", "/help/index", 5)
        self.menu.add_item(_("Developer's Manual"), "icon-info-sign", "/help/view/plinth", 10)
        self.menu.add_item(_("FAQ"), "icon-question-sign", "/help/view/faq", 20)
        self.menu.add_item(_("%s Wiki" % cfg.box_name), "icon-pencil", "http://wiki.debian.org/FreedomBox", 30)
	self.menu.add_item(_("About"), "icon-star", "/help/about", 100)

    @cherrypy.expose
    def index(self):
        return util.render_template(template='help',
                                    title=_('Documentation and FAQ'))

    @cherrypy.expose
    def about(self):
        return util.render_template(
            template='about',
            title=_('About the {box_name}').format(box_name=cfg.box_name))


class View(PagePlugin):
    def __init__(self, *args, **kwargs):
        PagePlugin.__init__(self, *args, **kwargs)
        self.register_page("help.view")

    @cherrypy.expose
    def default(self, page=''):
        if page not in ['design', 'plinth', 'hacking', 'faq']:
            raise cherrypy.HTTPError(404, "The path '/help/view/%s' was not found." % page)

        with open(os.path.join("doc", "%s.part.html" % page), 'r') as IF:
            main = IF.read()
        return util.render_template(title=_("%s Documentation" %
                                            cfg.product_name), main=main)
