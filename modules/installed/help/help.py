import os
import cherrypy
from gettext import gettext as _
from plugin_mount import PagePlugin
import cfg
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
        main="""
        <p>There are a variety of places to go for help with Plinth
        and the box it runs on.</p>

        <p>This front end has a <a
        href="/help/view/plinth">developer's manual</a>.  It isn't
        complete, but it is the first place to look.  Feel free to
        offer suggestions, edits, and screenshots for completing
        it!</p>

        <p><a href="http://wiki.debian.org/FreedomBox" target="_blank">A section of
        the Debian wiki</a> is devoted to the %(box)s.  At some
        point the documentation in the wiki and the documentation in
        the manual should dovetail.</p>

        <p>There
        are Debian gurus in the \#debian channels of both
        irc.freenode.net and irc.oftc.net.  They probably don't know
        much about the %(box)s and almost surely know nothing of
        this front end, but they are an incredible resource for
        general Debian issues.</p>

        <p>There is no <a href="/help/view/faq">FAQ</a> because
        the question frequency is currently zero for all
        questions.</p>
        """ % {'box':cfg.box_name}
        return self.fill_template(title="Documentation and FAQ", main=main)

    @cherrypy.expose
    def about(self):
        return self.fill_template(title=_("About the %s" % cfg.box_name), main="""
        <img src="/static/theme/img/freedombox-logo-250px.png" class="main-graphic" />
        <p>We live in a world where our use of the network is
        mediated by those who often do not have our best
        interests at heart. By building software that does not rely on
        a central service, we can regain control and privacy. By
        keeping our data in our homes, we gain useful legal
        protections over it. By giving back power to the users over
        their networks and machines, we are returning the Internet to
        its intended peer-to-peer architecture.</p>

	<p>In order to bring about the new network order, it is
	paramount that it is easy to convert to it. The hardware it
	runs on must be cheap. The software it runs on must be easy to
	install and administrate by anybody. It must be easy to
	transition from existing services.</p>
	<p><a class="btn btn-primary btn-large" href="http://wiki.debian.org/FreedomBox" target="_blank">Learn more &raquo;</a></p>""",
	sidebar_right=_("""<strong>Our Goal</strong><p>There are a number of projects working to realize a future
	of distributed services; we aim to bring them all together in
	a convenient package.</p>

	<p>For more information about the FreedomBox project, see the
	<a href="http://wiki.debian.org/FreedomBox">Debian
	Wiki</a>.</p>
	"""))

class View(PagePlugin):
    def __init__(self, *args, **kwargs):
        PagePlugin.__init__(self, *args, **kwargs)
        self.register_page("help.view")

    @cherrypy.expose
    def default(self, page=''):
        if page not in ['design', 'plinth', 'hacking', 'faq']:
            raise cherrypy.HTTPError(404, "The path '/help/view/%s' was not found." % page)
            return self.fill_template(template="err", main="<p>Sorry, as much as I would like to show you that page, I don't seem to have a page named %s!</p>" % page)
        IF = open(os.path.join("doc", "%s.part.html" % page), 'r')
        main = IF.read()
        IF.close()
        return self.fill_template(template="two_col", title=_("%s Documentation" % cfg.product_name), main=main)
