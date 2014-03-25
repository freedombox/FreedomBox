import cherrypy
from modules.auth import require
import cfg
from util import *
import util as u

class PluginMount(type):
    """See http://martyalchin.com/2008/jan/10/simple-plugin-framework/ for documentation"""
    def __init__(cls, name, bases, attrs):
        if not hasattr(cls, 'plugins'):
            cls.plugins = []
        else:
            cls.plugins.append(cls)

    def init_plugins(cls, *args, **kwargs):
        try:
            cls.plugins = sorted(cls.plugins, key=lambda x: x.order, reverse=False)
        except AttributeError:
            pass
        return [p(*args, **kwargs) for p in cls.plugins]
    def get_plugins(cls, *args, **kwargs):
        return cls.init_plugins(*args, **kwargs)

class MultiplePluginViolation:
    pass

class PluginMountSingular(PluginMount):
    def __init__(cls, name, bases, attrs):
        if not hasattr(cls, 'plugins'):
            cls.plugins = []
        else:
            if len(cls.plugins) > 0:
                raise MultiplePluginViolation
            cls.plugins.append(cls)
            

def get_parts(obj, parts=None, *args, **kwargs):
    if parts == None:
        parts={}

    fields = ['sidebar_left', 'sidebar_right', 'main', 'js', 'onload', 'nav', 'css', 'title']
    for v in fields:
        if not v in parts:
            parts[v] = ''
        exec("""
try:
    if str(type(obj.%(v)s))=="<type 'instancemethod'>":
        parts[v] += obj.%(v)s(*args, **kwargs)
    else:
        parts[v] += obj.%(v)s
except AttributeError:
    pass""" % {'v':v})

    return parts

class PagePlugin:
    """
    Mount point for page plugins.  Page plugins provide display pages
    in the interface (one menu item, for example).

    order - How early should this plugin be loaded?  Lower order is earlier.
    """

    order = 50

    __metaclass__ = PluginMount
    def __init__(self, *args, **kwargs):
        """If cfg.html_root is none, then this is the html_root."""
        if not cfg.html_root:
            cfg.log('Setting html root to %s' % self.__class__.__name__)
            cfg.html_root = self
            
    def register_page(self, url):
        cfg.log.info("Registering page: %s" % url)
        exec "cfg.html_root.%s = self" % (url)
    def fill_template(self, *args, **kwargs):
        return u.page_template(*args, **kwargs)

    def forms(self, url, *args, **kwargs):
        for form in cfg.forms:
            if url in form.url:
                cfg.log('Pulling together form for url %s (which matches %s)' % (url, form.url))

                parts = get_parts(form, None, *args, **kwargs)

        return parts
        return {'sidebar_left':left, 'sidebar_right':right, 'main':main}

class FormPlugin():
    """
    Mount point for plugins that provide forms at specific URLs.

    Form plugin classes should also inherit from PagePlugin so they
    can implement the page that handles the results of the form.  The
    name of the class will be appended to each url where the form is
    displayed to get the urls of the results pages.

    Plugins implementing this reference should provide the following attributes:

    url - list of URL path strings of pages on which to display this
    form, not including the url path that *only* displays this form
    (that's handled by the index method)

    order - How high up on the page should this content be displayed?
    Lower order is higher up.

    The following attributes are optional (though without at least one
    of them, this plugin won't do much):

    sidebar_right - text to be displayed in the right column (can be attribute or method) (optional)

    sidebar_left - text to be displayed in the left column  (can be attribute or method) (optional)

    main - text to be displayed in the center column (i.e. the form) (can be attribute or method)

    js - attribute containing a string that will be placed in the
    template head, just below the javascript loads.  Use it to load
    more javascript files (optional)

    Although this plugin is intended for forms, it could just display
    some html and skip the form.
    """
    __metaclass__ = PluginMount

    order = 50
    url = []
    js = ''

    def __init__(self, *args, **kwargs):
        for u in self.url:
            exec "cfg.html_root.%s = self" % "%s.%s" % ('.'.join(u.split("/")[1:]), self.__class__.__name__)
            cfg.log("Registered page: %s.%s" % ('.'.join(u.split("/")[1:]), self.__class__.__name__))
            
    def main(self, *args, **kwargs):
        return "<p>Override this method and replace it with a form.</p>"

    @cherrypy.expose
    @require()
    def index(self, **kwargs):
        """If the user has tried to fill in the form, process it, otherwise, just display a default form."""
        if kwargs:
            kwargs['message'] = self.process_form(**kwargs)
        parts = get_parts(self, **kwargs)
        return self.fill_template(**parts)
                                  
    def process_form(self, **kwargs):
        """Process the form.  Return any message as a result of processing."""
        pass

    def fill_template(self, *args, **kwargs):
        if not 'js' in kwargs:
            try:
                kwargs['js'] = self.js
            except AttributeError:
                pass
        cfg.log("%%%%%%%%%%% %s" % kwargs)
        return u.page_template(*args, **kwargs)

class UserStoreModule:
    """
    Mount Point for plugins that will manage the user backend storage,
    where we keep a hash for each user.

    Plugins implementing this reference should provide the following
    methods, as described in the doc strings of the default
    user_store.py: get, get_all, set, exists, remove, attr, expert.
    See source code for doc strings.

    This is designed as a plugin so mutiple types of user store can be
    supported.  But the project is moving towards LDAP for
    compatibility with third party software.  A future version of
    Plinth is likely to require LDAP.
    """
    __metaclass__ = PluginMountSingular # singular because we can only use one user store at a time

