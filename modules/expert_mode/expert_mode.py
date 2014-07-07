from django import forms
from django.contrib import messages
from django.template.response import TemplateResponse
from gettext import gettext as _

import cfg
from ..lib.auth import login_required


class ExpertsForm(forms.Form):  # pylint: disable-msg=W0232
    """Form to configure expert mode"""
    expert_mode = forms.BooleanField(
        label=_('Expert Mode'), required=False)


def init():
    """Initialize the module"""
    menu = cfg.main_menu.find('/sys')
    menu.add_item(_('Expert Mode'), 'icon-cog', '/sys/expert', 10)


@login_required
def index(request):
    """Serve the configuration form"""
    status = get_status(request)

    form = None

    if request.method == 'POST':
        form = ExpertsForm(request.POST, prefix='experts')
        # pylint: disable-msg=E1101
        if form.is_valid():
            _apply_changes(request, form.cleaned_data)
            status = get_status(request)
            form = ExpertsForm(initial=status, prefix='experts')
    else:
        form = ExpertsForm(initial=status, prefix='experts')

    return TemplateResponse(request, 'expert_mode.html',
                            {'title': _('Expert Mode'),
                             'form': form})


def get_status(request):
    """Return the current status"""
    return {'expert_mode': cfg.users.expert(request=request)}


def _apply_changes(request, new_status):
    """Apply expert mode configuration"""
    message = (messages.info, _('Settings unchanged'))

    user = cfg.users.current(request=request)

    if new_status['expert_mode']:
        if not 'expert' in user['groups']:
            user['groups'].append('expert')
            message = (messages.success, _('Expert mode enabled'))
    else:
        if 'expert' in user['groups']:
            user['groups'].remove('expert')
            message = (messages.success, _('Expert mode disabled'))

    cfg.users.set(user['username'], user)
    message[0](request, message[1])
