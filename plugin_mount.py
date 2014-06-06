import cfg


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
            

def _setattr_deep(obj, path, value):
    """If path is 'x.y.z' or ['x', 'y', 'z'] then perform obj.x.y.z = value"""
    if isinstance(path, basestring):
        path = path.split('.')

    for part in path[:-1]:
        obj = getattr(obj, part)

    setattr(obj, path[-1], value)


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
        _setattr_deep(cfg.html_root, url, self)


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

