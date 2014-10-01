"""First Boot: Initial Plinth Configuration.

See docs/design/first-connection.mdwn for details.

The Plinth first-connection process has several stages:

0. The user connects to Plinth for the first time and is redirected from
   the home page to the Hello page.

1. The user sets the Box's name, the administrator user name and password.

2. The user interacts with the box normally.

"""

from django import forms
from django.contrib import messages
from django.core import validators
from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect
from django.template.response import TemplateResponse
from gettext import gettext as _

from plinth.modules.config import config
from plinth.modules.lib.auth import add_user
from plinth import kvstore


class State0Form(forms.Form):  # pylint: disable-msg=W0232
    """First boot state 0 form"""

    hostname = forms.CharField(
        label=_('Name your FreedomBox'),
        help_text=_('For convenience, your FreedomBox needs a name.  It \
should be something short that does not contain spaces or punctuation. \
"Willard" would be a good name while "Freestyle McFreedomBox!!!" would \
not. It must be alphanumeric, start with an alphabet and must not be greater \
than 63 characters in length.'),
        validators=[
            validators.RegexValidator(r'^[a-zA-Z][a-zA-Z0-9]{,62}$',
                                      _('Invalid hostname'))])

    username = forms.CharField(label=_('Username'))
    password = forms.CharField(label=_('Password'),
                               widget=forms.PasswordInput())


def index(request):
    """Serve the index first boot page"""
    return state0(request)


def state0(request):
    """In this state, configure hostname and administrator username and
    password.

    All the parameters are form inputs.  They get passed in when the form is
    submitted.  This method checks the inputs and if they validate, uses them
    to take action.  If they do not validate, it displays the form to give the
    user a chance to input correct values.  It might display an error message.

    """
    try:
        if kvstore.get_default('firstboot_state', 0) >= 5:
            return HttpResponseRedirect(reverse('index'))
    except KeyError:
        pass

    # Until LDAP is in place, we'll put the box key in the cfg.store_file
    status = get_state0()

    form = None

    if request.method == 'POST':
        form = State0Form(request.POST, prefix='firstboot')
        # pylint: disable-msg=E1101
        if form.is_valid():
            success = _apply_state0(request, status, form.cleaned_data)

            if success:
                # Everything is good, permanently mark and move to page 2
                kvstore.set('firstboot_state', 1)
                return HttpResponseRedirect(reverse('first_boot:state1'))
    else:
        form = State0Form(initial=status, prefix='firstboot')

    return TemplateResponse(request, 'firstboot_state0.html',
                            {'title': _('First Boot!'),
                             'form': form})


def get_state0():
    """Return the state for form state 0"""
    return {'hostname': config.get_hostname()}


def _apply_state0(request, old_state, new_state):
    """Apply changes in state 0 form"""
    success = True

    if old_state['hostname'] != new_state['hostname']:
        config.set_hostname(new_state['hostname'])

    error = add_user(new_state['username'], new_state['password'],
                     'First user, please change', '', True)
    if error:
        messages.error(request, _('User account creation failed: %s') % error)
        success = False
    else:
        messages.success(request, _('User account created'))

    return success


def state1(request):
    """State 1 is when we have a hostname and administrator account. Redirect
    the user to login page after this.

    """
    # TODO complete first_boot handling
    # Make sure the user is not stuck on a dead end for now.
    kvstore.set('firstboot_state', 5)

    return TemplateResponse(request, 'firstboot_state1.html',
                            {'title': _('Setup Complete')})
