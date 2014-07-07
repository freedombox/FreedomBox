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


class MultiplePluginViolation(Exception):
    """Multiple plugins found for a type where only one is expected"""
    pass


class PluginMountSingular(PluginMount):
    """Plugin mounter that allows only one plugin of this meta type"""
    def __init__(cls, name, bases, attrs):
        if not hasattr(cls, 'plugins'):
            cls.plugins = []
        else:
            if len(cls.plugins) > 0:
                raise MultiplePluginViolation
            cls.plugins.append(cls)


class UserStoreModule(object):
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
    # Singular because we can only use one user store at a time
    __metaclass__ = PluginMountSingular
