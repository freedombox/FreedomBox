"""
First Boot: Initial Plinth Configuration.

See docs/design/first-connection.mdwn for details.

The Plinth first-connection process has several stages:

0. The user connects to Plinth for the first time and is redirected from
   the home page to the Hello page.

1. The user sets the Box's name, the administrator's name and
   password, and the box's PGP key (optional).

2. The box generates and the user receives any PGP keys.

3. The box detects the network's configuration and restarts networking.

4. The user interacts with the box normally.
"""

from django import forms
from django.contrib import messages
from django.core import validators
from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect
from django.template.response import TemplateResponse
from gettext import gettext as _

from ..lib.auth import add_user
from ..config import config
from withsqlite.withsqlite import sqlite_db
import cfg


## TODO: flesh out these tests values
def valid_box_key(value):
    """Check whether box key is valid"""
    del value  # Unused

    return True


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

    box_key = forms.CharField(
        label=_('Box\'s key (optional)'), required=False,
        widget=forms.Textarea(), validators=[valid_box_key],
        help_text=_('Cryptographic keys are used so that Box\'s identity can \
proved when talking to you.  This key can be auto-generated, but if one \
already exists (from a prior FreedomBox, for example), you can paste it \
below.  This key should not be the same as your key because you are not your \
FreedomBox!'))


def index(request):
    """Serve the index first boot page"""
    return state0(request)


def generate_box_key():
    """Generate a box key"""
    return "fake key"


def state0(request):
    """
    In this state, we do time config over HTTP, name the box and
    server key selection.

    All the parameters are form inputs.  They get passed in when
    the form is submitted.  This method checks the inputs and if
    they validate, uses them to take action.  If they do not
    validate, it displays the form to give the user a chance to
    input correct values.  It might display an error message (in
    the message parameter).

    message is an optional string that we can display to the
    user. It's a good place to put error messages.
    """
    try:
        if _read_state() >= 5:
            return HttpResponseRedirect(reverse('index'))
    except KeyError:
        pass

    ## Until LDAP is in place, we'll put the box key in the cfg.store_file
    status = get_state0()

    form = None

    if request.method == 'POST':
        form = State0Form(request.POST, prefix='firstboot')
        # pylint: disable-msg=E1101
        if form.is_valid():
            success = _apply_state0(request, status, form.cleaned_data)

            if success:
                # Everything is good, permanently mark and move to page 2
                _write_state(1)
                return HttpResponseRedirect(reverse('first_boot:state1'))
    else:
        form = State0Form(initial=status, prefix='firstboot')

    return TemplateResponse(request, 'firstboot_state0.html',
                            {'title': _('First Boot!'),
                             'form': form})


def get_state0():
    """Return the state for form state 0"""
    with sqlite_db(cfg.store_file, table="thisbox", autocommit=True) as \
            database:
        return {'hostname': config.get_hostname(),
                'box_key': database.get('box_key', None)}


def _apply_state0(request, old_state, new_state):
    """Apply changes in state 0 form"""
    success = True
    with sqlite_db(cfg.store_file, table="thisbox", autocommit=True) as \
            database:
        database['about'] = 'Information about this FreedomBox'

        if new_state['box_key']:
            database['box_key'] = new_state['box_key']
        elif not old_state['box_key']:
            database['box_key'] = generate_box_key()

        if old_state['hostname'] != new_state['hostname']:
            config.set_hostname(new_state['hostname'])

        error = add_user(new_state['username'], new_state['password'],
                         'First user, please change', '', True)
        if error:
            messages.error(
                request, _('User account creation failed: %s') % error)
            success = False
        else:
            messages.success(request, _('User account created'))

    return success


def state1(request):
    """
    State 1 is when we have a box name and key.  In this state,
    our task is to provide a certificate and maybe to guide the
    user through installing it.  We automatically move to State 2,
    which is an HTTPS connection.

    TODO: HTTPS failure in State 2 should returns to state 1.
    """
    # TODO complete first_boot handling
    # Make sure the user is not stuck on a dead end for now.
    _write_state(5)

    return TemplateResponse(request, 'firstboot_state1.html',
                            {'title': _('Installing the Certificate')})


def _read_state():
    """Read the current state from database"""
    with sqlite_db(cfg.store_file, table='firstboot',
                   autocommit=True) as database:
        return database['state']


def _write_state(state):
    """Write state to database"""
    with sqlite_db(cfg.store_file, table='firstboot',
                   autocommit=True) as database:
        database['state'] = state
