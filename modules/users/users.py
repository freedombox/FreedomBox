from django import forms
from django.contrib import messages
from django.core import validators
from django.template import RequestContext
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
from gettext import gettext as _

import cfg
from ..lib.auth import add_user, login_required
from model import User


def init():
    """Intialize the module"""
    menu = cfg.main_menu.find('/sys')
    menu.add_item(_('Users and Groups'), 'icon-user', '/sys/users', 15)


@login_required
def index(request):
    """Return a rendered users page"""
    menu = {'title': _('Users and Groups'),
            'items': [{'url': '/sys/users/add',
                       'text': _('Add User')},
                      {'url': '/sys/users/edit',
                       'text': _('Edit Users')}]}

    sidebar_right = render_to_string('menu_block.html', {'menu': menu},
                                     RequestContext(request))

    return TemplateResponse(request, 'login_nav.html',
                            {'title': _('Manage Users and Groups'),
                             'sidebar_right': sidebar_right})


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


@login_required
def add(request):
    """Serve the form"""
    form = None

    if request.method == 'POST':
        form = UserAddForm(request.POST, prefix='user')
        # pylint: disable-msg=E1101
        if form.is_valid():
            _add_user(request, form.cleaned_data)
            form = UserAddForm(prefix='user')
    else:
        form = UserAddForm(prefix='user')

    return TemplateResponse(request, 'users_add.html',
                            {'title': _('Add User'),
                             'form': form})


def _add_user(request, data):
    """Add a user"""
    if cfg.users.exists(data['username']):
        messages.error(request, _('User "{username}" already exists').format(
            username=data['username']))
        return

    add_user(data['username'], data['password'], data['full_name'],
             data['email'], False)
    messages.success(request, _('User "{username}" added').format(
        username=data['username']))


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


@login_required
def edit(request):
    """Serve the edit form"""
    form = None

    if request.method == 'POST':
        form = UserEditForm(request.POST, prefix='user')
        # pylint: disable-msg=E1101
        if form.is_valid():
            _apply_edit_changes(request, form.cleaned_data)
            form = UserEditForm(prefix='user')
    else:
        form = UserEditForm(prefix='user')

    return TemplateResponse(request, 'users_edit.html',
                            {'title': _('Edit or Delete User'),
                             'form': form})


def _apply_edit_changes(request, data):
    """Apply form changes"""
    for field, value in data.items():
        if not value:
            continue

        if not field.startswith('delete_user_'):
            continue

        username = field.split('delete_user_')[1]

        requesting_user = request.session.get(cfg.session_key, None)
        cfg.log.info('%s asked to delete %s' %
                     (requesting_user, username))

        if username == cfg.users.current(request=request, name=True):
            messages.error(
                request, _('Can not delete current account - "%s"') % username)
            continue

        if not cfg.users.exists(username):
            messages.error(request, _('User "%s" does not exist') % username)
            continue

        try:
            cfg.users.remove(username)
            messages.success(request, _('User "%s" deleted') % username)
        except IOError as exception:
            messages.error(request, _('Error deleting "%s" - %s') %
                           (username, exception))
