from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse_lazy
from django.template import RequestContext
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
from gettext import gettext as _
import logging

from plinth import actions
from plinth import cfg
from plinth import service


LOGGER = logging.getLogger(__name__)

SIDE_MENU = {
    'title': _('XMPP'),
    'items': [
        {
            'url': reverse_lazy('xmpp:configure'),
            'text': _('Configure XMPP Server'),
        },
        {
            'url': reverse_lazy('xmpp:register'),
            'text': _('Register XMPP Account'),
        }
    ]
}


def init():
    """Initialize the XMPP module"""
    menu = cfg.main_menu.get('apps:index')
    menu.add_item('Chat', 'icon-comment', '/../jwchat', 20)
    menu.add_urlname('XMPP', 'icon-comment', 'xmpp:index', 40)

    service.Service(
        'xmpp-client', _('Chat Server - client connections'),
        is_external=True, enabled=True)
    service.Service(
        'xmpp-server', _('Chat Server - server connections'),
        is_external=True, enabled=True)
    service.Service(
        'xmpp-bosh', _('Chat Server - web interface'), is_external=True,
        enabled=True)


@login_required
def index(request):
    """Serve XMPP page"""
    main = "<p>XMPP Server Accounts and Configuration</p>"

    sidebar_right = render_to_string('menu_block.html', {'menu': SIDE_MENU},
                                     RequestContext(request))

    return TemplateResponse(request, 'base.html',
                            {'title': _('XMPP Server'),
                             'main': main,
                             'sidebar_right': sidebar_right})


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

    sidebar_right = render_to_string('menu_block.html', {'menu': SIDE_MENU},
                                     RequestContext(request))

    return TemplateResponse(request, 'xmpp_configure.html',
                            {'title': _('Configure XMPP Server'),
                             'form': form,
                             'sidebar_right': sidebar_right})


def get_status():
    """Return the current status"""
    output = actions.run('xmpp-setup', 'status')
    return {'inband_enabled': 'inband_enable' in output.split()}


def _apply_changes(request, old_status, new_status):
    """Apply the form changes"""
    LOGGER.info('Status - %s, %s', old_status, new_status)

    if old_status['inband_enabled'] == new_status['inband_enabled']:
        messages.info(request, _('Setting unchanged'))
        return

    if new_status['inband_enabled']:
        messages.success(request, _('Inband registration enabled'))
        option = 'inband_enable'
    else:
        messages.success(request, _('Inband registration disabled'))
        option = 'noinband_enable'

    LOGGER.info('Option - %s', option)
    actions.superuser_run('xmpp-setup', [option])


class RegisterForm(forms.Form):  # pylint: disable-msg=W0232
    """Configuration form"""
    username = forms.CharField(label=_('Username'))

    password = forms.CharField(
        label=_('Password'), widget=forms.PasswordInput())


@login_required
def register(request):
    """Serve the registration form"""
    form = None

    if request.method == 'POST':
        form = RegisterForm(request.POST, prefix='xmpp')
        # pylint: disable-msg=E1101
        if form.is_valid():
            _register_user(request, form.cleaned_data)
            form = RegisterForm(prefix='xmpp')
    else:
        form = RegisterForm(prefix='xmpp')

    sidebar_right = render_to_string('menu_block.html', {'menu': SIDE_MENU},
                                     RequestContext(request))

    return TemplateResponse(request, 'xmpp_register.html',
                            {'title': _('Register XMPP Account'),
                             'form': form,
                             'sidebar_right': sidebar_right})


def _register_user(request, data):
    """Register a new XMPP user"""
    output = actions.superuser_run(
        'xmpp-register', [data['username'], data['password']])

    if 'successfully registered' in output:
        messages.success(request, _('Registered account for %s') %
                         data['username'])
    else:
        messages.error(request,
                       _('Failed to register account for %s: %s') %
                       (data['username'], output))
