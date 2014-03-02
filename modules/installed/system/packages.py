import cherrypy
from gettext import gettext as _
from auth import require
from plugin_mount import PagePlugin, FormPlugin
from forms import Form
import actions
import cfg
from util import Message

class Packages(PagePlugin, FormPlugin):
    order = 20

    def __init__(self, *args, **kwargs):
        PagePlugin.__init__(self, *args, **kwargs)
        self.register_page("sys.packages")
        cfg.html_root.sys.menu.add_item("Package Manager", "icon-gift", "/sys/packages", 20)

    @cherrypy.expose
    @require()
    def index(self, *args, **kwargs):
        output, error = actions.run("module-manager", ["list-available"])
        if error:
            raise Exception("something is wrong: " + error)
        modules_available = output.split()
        
        output, error = actions.run("module-manager", \
                                    ["list-enabled", cfg.python_root])
        if error:
            raise Exception("something is wrong: " + error)
        modules_enabled = output.split()

        if 'submitted' in kwargs:
            del kwargs['submitted']
            modules_selected = map(lambda x: x.split("_")[0], kwargs.keys())
            for module in modules_available:
                if module in modules_enabled:
                    if module not in modules_selected:
                        output, error = actions.superuser_run(\
                                "module-manager",\
                                ["disable", cfg.python_root, module])
                        # TODO: need a smoother way for plinth
                        # to unload the module
                else:
                    if module in modules_selected:
                        output, error = actions.superuser_run(\
                                "module-manager",\
                                ["enable", cfg.python_root, module])
                        # TODO: need to get plinth to load
                        # the module we just enabled

        main = _("""
<p>aptitude purge modules</p>
<p>aptitude install modules</p>
<p>The modules should depend on the appropriate Debian packages.</p>""")
        main += self.form(self, Message(output), args, kwargs)
        sidebar_right = _("""
<strong>Help</strong>
<p>On this page, you can add or remove %s plugins to your %s.</p>
<p>Plugins are just Debian packages, so Debian's usual package management features should make this job fairly easy.</p>""" % (cfg.product_name, cfg.box_name))
        return self.fill_template(title=_("Add/Remove Plugins"), main=main, sidebar_right=sidebar_right)

    def form(self, message=None, *args, **kwargs):
        output, error = actions.run("module-manager", ["list-available"])
        if error:
            raise Exception("something is wrong: " + error)
        modules_available = output.split()
        
        output, error = actions.run("module-manager",\
                                    ["list-enabled", cfg.python_root])
        if error:
            raise Exception("something is wrong: " + error)
        modules_enabled = output.split()

        form = Form(title="Manage Plugins",
                    action=cfg.server_dir + "/sys/packages/index",
                    name="manage_modules",
                    message=message)
        for module in modules_available:
            form.checkbox(_("Enable %s" % module), name="%s_enable" % module, id="%s_enable" % module, checked = True if module in modules_enabled else False)
        form.hidden(name="submitted", value="True")
        form.html(_("""<p>Enabling a plugin will cause a corresponding page to appear in Plinth.</p>"""))
        form.submit(_("Update setup"))
        return form.render()
