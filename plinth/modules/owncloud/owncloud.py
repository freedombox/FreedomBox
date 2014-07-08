from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.template.response import TemplateResponse
from gettext import gettext as _

from plinth import actions
from plinth import cfg
from plinth import service


SERVICE = None


class OwnCloudForm(forms.Form):  # pylint: disable-msg=W0232
    """ownCloud configuration form"""
    enabled = forms.BooleanField(label=_('Enable ownCloud'), required=False)


def init():
    """Initialize the ownCloud module"""
    menu = cfg.main_menu.get('apps:index')
    menu.add_urlname('Owncloud', 'icon-picture', 'owncloud:index', 35)

    status = get_status()

    global SERVICE  # pylint: disable-msg=W0603
    SERVICE = service.Service('owncloud', _('ownCloud'), ['http', 'https'],
                              is_external=True, enabled=status['enabled'])


@login_required
def index(request):
    """Serve the ownCloud configuration page"""
    status = get_status()

    form = None

    if request.method == 'POST':
        form = OwnCloudForm(request.POST, prefix='owncloud')
        # pylint: disable-msg=E1101
        if form.is_valid():
            _apply_changes(request, status, form.cleaned_data)
            status = get_status()
            form = OwnCloudForm(initial=status, prefix='owncloud')
    else:
        form = OwnCloudForm(initial=status, prefix='owncloud')

    return TemplateResponse(request, 'owncloud.html',
                            {'title': _('ownCloud'),
                             'form': form})


def get_status():
    """Return the current status"""
    output = actions.run('owncloud-setup', 'status')
    return {'enabled': 'enable' in output.split()}


def _apply_changes(request, old_status, new_status):
    """Apply the changes"""
    if old_status['enabled'] == new_status['enabled']:
        messages.info(request, _('Setting unchanged'))
        return

    if new_status['enabled']:
        messages.success(request, _('ownCloud enabled'))
        option = 'enable'
    else:
        messages.success(request, _('ownCloud disabled'))
        option = 'noenable'

    actions.superuser_run('owncloud-setup', [option], async=True)

    # Send a signal to other modules that the service is
    # enabled/disabled
    SERVICE.notify_enabled(None, new_status['enabled'])
