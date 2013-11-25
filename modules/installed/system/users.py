import os, cherrypy
from gettext import gettext as _
from auth import require, add_user
from plugin_mount import PagePlugin, FormPlugin
import cfg
from forms import Form
from util import *
from model import User

class users(PagePlugin):
    order = 20 # order of running init in PagePlugins
    def __init__(self, *args, **kwargs):
        PagePlugin.__init__(self, *args, **kwargs)
        self.register_page("sys.users")
        self.register_page("sys.users.add")
        self.register_page("sys.users.edit")

    @cherrypy.expose
    @require()
    def index(self):
        sidebar_right = '<strong><a href="'+cfg.server_dir+'/sys/users/add">Add User</a></strong><br/><strong><a href="'+cfg.server_dir+'/sys/users/edit">Edit Users</a></strong>'
        return self.fill_template(title="Manage Users and Groups", sidebar_right=sidebar_right)

class add(FormPlugin, PagePlugin):
    url = ["/sys/users/add"]
    order = 30

    sidebar_left = ''
    sidebar_right = _("""<strong>Add User</strong><p>Adding a user via this
        administrative interface <strong>might</strong> create a system user.
        For example, if you provide a user with ssh access, she will
        need a system account.  If you don't know what that means,
        don't worry about it.</p>""")

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
        msg = Message()

        error = add_user(username, password, name, email, False)
        if error:
            msg.text = error
        else:
            msg.add = _("%s saved." % username)

        cfg.log(msg.text)
        main = self.main(username, name, email, msg=msg.text)
        return self.fill_template(title="Manage Users and Groups", main=main, sidebar_left=self.sidebar_left, sidebar_right=self.sidebar_right)

class edit(FormPlugin, PagePlugin):
    url = ["/sys/users/edit"]
    order = 35

    sidebar_left = ''
    sidebar_right = _("""<strong>Edit Users</strong><p>Click on a user's name to
    go to a screen for editing that user's account.</p><strong>Delete
    Users</strong><p>Check the box next to a users' names and then click
    "Delete User" to remove users from %s and the %s
    system.</p><p>Deleting users is permanent!</p>""" % (cfg.product_name, cfg.box_name))

    def main(self, msg=''):
        users = cfg.users.get_all()
        add_form = Form(title=_("Edit or Delete User"), action=cfg.server_dir + "/sys/users/edit", message=msg)
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
            msg = Message()
            usernames = find_keys(kwargs, 'on')
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
            main = self.main(msg=msg.text)
            return self.fill_template(title="Manage Users and Groups", main=main, sidebar_left=self.sidebar_left, sidebar_right=self.sidebar_right)

        sidebar_right = ''
        u = cfg.users[kwargs['username']]
        if not u:
            main = _("<p>Could not find a user with username of %s!</p>" % kwargs['username'])
            return self.fill_template(template="err", title=_("Unknown User"), main=main,
                             sidebar_left=self.sidebar_left, sidebar_right=sidebar_right)

        main = _("""<strong>Edit User '%s'</strong>""" % u['username'])
        sidebar_right = ''
        return self.fill_template(title="Manage Users and Groups", main=main, sidebar_left=self.sidebar_left, sidebar_right=sidebar_right)
