#
# This file is part of Plinth.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse_lazy
from django.template.response import TemplateResponse
from gettext import gettext as _
import logging

from plinth import actions
from plinth import cfg
from plinth import package
from plinth import service
from plinth.signals import pre_hostname_change, post_hostname_change
from plinth.signals import domainname_change


LOGGER = logging.getLogger(__name__)

subsubmenu = [{'url': reverse_lazy('xmpp:index'),
               'text': _('About')},
              {'url': reverse_lazy('xmpp:configure'),
               'text': _('Configure XMPP Server')},
              {'url': reverse_lazy('xmpp:register'),
               'text': _('Register XMPP Account')}]


def init():
    """Initialize the XMPP module"""
    menu = cfg.main_menu.get('apps:index')
    menu.add_urlname('XMPP', 'glyphicon-comment', 'xmpp:index', 40)

    service.Service(
        'xmpp-client', _('Chat Server - client connections'),
        is_external=True, enabled=True)
    service.Service(
        'xmpp-server', _('Chat Server - server connections'),
        is_external=True, enabled=True)
    service.Service(
        'xmpp-bosh', _('Chat Server - web interface'), is_external=True,
        enabled=True)

    pre_hostname_change.connect(on_pre_hostname_change)
    post_hostname_change.connect(on_post_hostname_change)
    domainname_change.connect(on_domainname_change)


@login_required
@package.required(['jwchat', 'ejabberd'])
def index(request):
    """Serve XMPP page"""
    return TemplateResponse(request, 'xmpp.html',
                            {'title': _('XMPP Server'),
                             'subsubmenu': subsubmenu})


class ConfigureForm(forms.Form):  # pylint: disable-msg=W0232
    """Configuration form"""
    inband_enabled = forms.BooleanField(
        label=_('Allow In-Band Registration'), required=False,
        help_text=_('When enabled, anyone who can reach this server will be \
allowed to register an account through an XMPP client'))


@login_required
def configure(request):
    """Serve the configuration form"""
    status = get_status()

    form = None

    if request.method == 'POST':
        form = ConfigureForm(request.POST, prefix='xmpp')
        # pylint: disable-msg=E1101
        if form.is_valid():
            _apply_changes(request, status, form.cleaned_data)
            status = get_status()
            form = ConfigureForm(initial=status, prefix='xmpp')
    else:
        form = ConfigureForm(initial=status, prefix='xmpp')

    return TemplateResponse(request, 'xmpp_configure.html',
                            {'title': _('Configure XMPP Server'),
                             'form': form,
                             'subsubmenu': subsubmenu})


def get_status():
    """Return the current status"""
    output = actions.run('xmpp-setup', ['status'])
    return {'inband_enabled': 'inband_enable' in output.split()}


def _apply_changes(request, old_status, new_status):
    """Apply the form changes"""
    LOGGER.info('Status - %s, %s', old_status, new_status)

    if old_status['inband_enabled'] == new_status['inband_enabled']:
        messages.info(request, _('Setting unchanged'))
        return

    if new_status['inband_enabled']:
        option = 'inband_enable'
    else:
        option = 'noinband_enable'

    LOGGER.info('Option - %s', option)
    output = actions.superuser_run('xmpp-setup', [option])

    if 'Failed' in output:
        messages.error(request,
                       _('Error when configuring XMPP server: %s') %
                       output)
    elif option == 'inband_enable':
        messages.success(request, _('Inband registration enabled'))
    else:
        messages.success(request, _('Inband registration disabled'))


class RegisterForm(forms.Form):  # pylint: disable-msg=W0232
    """Configuration form."""
    username = forms.CharField(label=_('Username'))
    vhost = forms.ChoiceField(
        label=_('Host'), choices=(),
        help_text=_('The new user will be able to login as: username@host'))
    password = forms.CharField(
        label=_('Password'), widget=forms.PasswordInput())

    def __init__(self, vhosts, *args, **kwargs):
        """Set the list of possible values for hosts."""
        super(RegisterForm, self).__init__(*args, **kwargs)

        self.fields['vhost'].choices = ((vhost, '@' + vhost)
                                        for vhost in vhosts)


@login_required
def register(request):
    """Serve the registration form."""
    form = None
    vhosts = actions.run('xmpp', ['get-vhosts']).split()

    if request.method == 'POST':
        form = RegisterForm(vhosts, request.POST, prefix='xmpp')
        # pylint: disable-msg=E1101
        if form.is_valid():
            _register_user(request, form.cleaned_data)
            form = RegisterForm(vhosts, prefix='xmpp')
    else:
        form = RegisterForm(vhosts, prefix='xmpp')

    return TemplateResponse(request, 'xmpp_register.html',
                            {'title': _('Register XMPP Account'),
                             'form': form,
                             'subsubmenu': subsubmenu})


def _register_user(request, data):
    """Register a new XMPP user"""
    output = actions.superuser_run(
        'xmpp',
        ['register',
         '--username', data['username'],
         '--vhost', data['vhost'],
         '--password', data['password']])

    if 'successfully registered' in output:
        messages.success(request, _('Registered account %s@%s') %
                         (data['username'], data['vhost']))
    else:
        messages.error(request,
                       _('Failed to register account %s@%s: %s') %
                       (data['username'], data['vhost'], output))


def on_pre_hostname_change(sender, old_hostname, new_hostname, **kwargs):
    """
    Backup ejabberd database before hostname is changed.
    """
    del sender  # Unused
    del kwargs  # Unused

    actions.superuser_run('xmpp',
                          ['pre-change-hostname',
                           '--old-hostname', old_hostname,
                           '--new-hostname', new_hostname])


def on_post_hostname_change(sender, old_hostname, new_hostname, **kwargs):
    """
    Update ejabberd and jwchat config after hostname is changed.
    """
    del sender  # Unused
    del kwargs  # Unused

    actions.superuser_run('xmpp',
                          ['change-hostname',
                           '--old-hostname', old_hostname,
                           '--new-hostname', new_hostname],
                          async=True)


def on_domainname_change(sender, old_domainname, new_domainname, **kwargs):
    """
    Update ejabberd and jwchat config after domain name is changed.
    """
    del sender  # Unused
    del old_domainname  # Unused
    del kwargs  # Unused

    actions.superuser_run('xmpp',
                          ['change-domainname',
                           '--domainname', new_domainname],
                          async=True)
