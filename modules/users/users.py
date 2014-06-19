import cherrypy
from django import forms
from django.core import validators
from gettext import gettext as _
from ..lib.auth import require, add_user
from plugin_mount import PagePlugin
import cfg
from model import User
import util


class Users(PagePlugin):
    order = 20 # order of running init in PagePlugins
    def __init__(self, *args, **kwargs):
        PagePlugin.__init__(self, *args, **kwargs)
        self.register_page("sys.users")

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


class UserAddForm(forms.Form):  # pylint: disable-msg=W0232
    """Form to add a new user"""

    username = forms.CharField(
        label=_('Username'),
        help_text=_('Must be lower case alphanumeric and start with \
and alphabet'),
        validators=[
            validators.RegexValidator(r'^[a-z][a-z0-9]*$',
                                      _('Invalid username'))])

    password = forms.CharField(label=_('Password'),
                               widget=forms.PasswordInput())
    full_name = forms.CharField(label=_('Full name'), required=False)
    email = forms.EmailField(label=_('Email'), required=False)


class UserAdd(PagePlugin):
    """Add user page"""
    order = 30

    def __init__(self, *args, **kwargs):
        PagePlugin.__init__(self, *args, **kwargs)

        self.register_page('sys.users.add')

    @cherrypy.expose
    @require()
    def index(self, **kwargs):
        """Serve the form"""
        form = None
        messages = []

        if kwargs:
            form = UserAddForm(kwargs, prefix='user')
            # pylint: disable-msg=E1101
            if form.is_valid():
                self._add_user(form.cleaned_data, messages)
                form = UserAddForm(prefix='user')
        else:
            form = UserAddForm(prefix='user')

        return util.render_template(template='users_add', title=_('Add User'),
                                    form=form, messages=messages)

    @staticmethod
    def _add_user(data, messages):
        """Add a user"""
        if cfg.users.exists(data['username']):
            messages.append(
                ('error', _('User "{username}" already exists').format(
                 username=data['username'])))
            return

        add_user(data['username'], data['password'], data['full_name'],
                 data['email'], False)
        messages.append(
            ('success', _('User "{username}" added').format(
             username=data['username'])))


class UserEditForm(forms.Form):  # pylint: disable-msg=W0232
    """Form to edit/delete a user"""
    def __init__(self, *args, **kwargs):
        # pylint: disable-msg=E1002
        super(forms.Form, self).__init__(*args, **kwargs)

        users = cfg.users.get_all()
        for uname in users:
            user = User(uname[1])

            label = '%s (%s)' % (user['name'], user['username'])
            field = forms.BooleanField(label=label, required=False)
            # pylint: disable-msg=E1101
            self.fields['delete_user_' + user['username']] = field


class UserEdit(PagePlugin):
    """User edit page"""
    order = 35

    def __init__(self, *args, **kwargs):
        PagePlugin.__init__(self, *args, **kwargs)

        self.register_page('sys.users.edit')

    @cherrypy.expose
    @require()
    def index(self, **kwargs):
        """Serve the form"""
        form = None
        messages = []

        if kwargs:
            form = UserEditForm(kwargs, prefix='user')
            # pylint: disable-msg=E1101
            if form.is_valid():
                self._apply_changes(form.cleaned_data, messages)
                form = UserEditForm(prefix='user')
        else:
            form = UserEditForm(prefix='user')

        return util.render_template(template='users_edit',
                                    title=_('Edit or Delete User'),
                                    form=form, messages=messages)

    @staticmethod
    def _apply_changes(data, messages):
        """Apply form changes"""
        for field, value in data.items():
            if not value:
                continue

            if not field.startswith('delete_user_'):
                continue

            username = field.split('delete_user_')[1]

            cfg.log.info('%s asked to delete %s' %
                         (cherrypy.session.get(cfg.session_key), username))

            if username == cfg.users.current(name=True):
                messages.append(
                    ('error',
                     _('Can not delete current account - "%s"') % username))
                continue

            if not cfg.users.exists(username):
                messages.append(('error',
                                 _('User "%s" does not exist') % username))
                continue

            try:
                cfg.users.remove(username)
                messages.append(('success', _('User "%s" deleted') % username))
            except IOError as exception:
                messages.append(('error', _('Error deleting "%s" - %s') %
                                 (username, exception)))
