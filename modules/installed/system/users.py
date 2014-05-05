import cherrypy
from gettext import gettext as _
from auth import require, add_user
from plugin_mount import PagePlugin, FormPlugin
import cfg
from forms import Form
from model import User
import util


class users(PagePlugin):
    order = 20 # order of running init in PagePlugins
    def __init__(self, *args, **kwargs):
        PagePlugin.__init__(self, *args, **kwargs)
        self.register_page("sys.users")
        self.register_page("sys.users.add")
        self.register_page("sys.users.edit")

    @staticmethod
    @cherrypy.expose
    @require()
    def index():
        """Return a rendered users page"""
        menu = {'title': _('Users and Groups'),
                'items': [{'url': '/sys/users/add',
                           'text': _('Add User')},
                          {'url': '/sys/users/edit',
                           'text': _('Edit Users')}]}
        sidebar_right = util.render_template(template='menu_block',
                                             menu=menu)
        return util.render_template(title="Manage Users and Groups",
                                    sidebar_right=sidebar_right)


class add(FormPlugin, PagePlugin):
    url = ["/sys/users/add"]
    order = 30

    @staticmethod
    def sidebar_right(**kwargs):
        """Return rendered string for sidebar on the right"""
        del kwargs  # Unused

        return util.render_template(template='users_add_sidebar')

    def main(self, username='', name='', email='', message=None, *args, **kwargs):
        form = Form(title="Add User",
                    action=cfg.server_dir + "/sys/users/add/index",
                    name="add_user_form",
                    message=message)
        form.text_input(_("Username"), name="username", value=username)
        form.text_input(_("Full name"), name="name", value=name)
        form.text_input(_("Email"), name="email", value=email)
        form.text_input(_("Password"), name="password", type="password")
        form.submit(label=_("Create User"), name="create")
        return form.render()

    def process_form(self, username=None, name=None, email=None, password=None, **kwargs):
        msg = util.Message()

        error = add_user(username, password, name, email, False)
        if error:
            msg.text = error
        else:
            msg.add(_("User %s added" % username))

        return msg.text


class edit(FormPlugin, PagePlugin):
    url = ["/sys/users/edit"]
    order = 35

    @staticmethod
    def sidebar_right(**kwargs):
        """Return rendered string for sidebar on the right"""
        del kwargs  # Unused

        return util.render_template(template='users_edit_sidebar')

    def main(self, message=None, **kwargs):
        users = cfg.users.get_all()
        add_form = Form(title=_("Edit or Delete User"),
                        action=cfg.server_dir + "/sys/users/edit",
                        message=message)
        add_form.html('<span class="indent"><strong>Delete</strong><br /></span>')
        for uname in users:
            user = User(uname[1])
            add_form.html('<span class="indent">&nbsp;&nbsp;%s&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;' %
                          add_form.get_checkbox(name=user['username']) +
                          '<a href="'+cfg.server_dir+'/sys/users/edit?username=%s">%s (%s)</a><br /></span>' %
                          (user['username'], user['name'], user['username']))
        add_form.submit(label=_("Delete User"), name="delete")
        return add_form.render()

    def process_form(self, **kwargs):
        if 'delete' in kwargs:
            msg = util.Message()
            usernames = util.find_keys(kwargs, 'on')
            cfg.log.info("%s asked to delete %s" % (cherrypy.session.get(cfg.session_key), usernames))
            if usernames:
                for username in usernames:
                    if cfg.users.exists(username):
                        try:
                            cfg.users.remove(username)
                            msg.add(_("Deleted user %s." % username))
                        except IOError, e:
                            if cfg.users.exists(username):
                                m = _("Error on deletion, user %s not fully deleted: %s" % (username, e))
                                cfg.log.error(m)
                                msg.add(m)
                            else:
                                m = _('Deletion failed on %s: %s' % (username, e))
                                cfg.log.error(m)
                                msg.add(m)
                    else:
                        cfg.log.warning(_("Can't delete %s.  User does not exist." % username))
                        msg.add(_("User %s does not exist." % username))
            else:
                msg.add = _("Must specify at least one valid, existing user.")

            return msg.txt

        if 'username' not in kwargs:
            return _('Invalid paramerters')

        if kwargs['username'] not in cfg.users:
            return _("<p>Could not find a user with username of %s!</p>") % \
                kwargs['username']

        user = cfg.users[kwargs['username']]
        return _("<strong>Edit User '%s'</strong>") % user['username']
