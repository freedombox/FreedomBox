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
from django.contrib import auth, messages
from django.core import validators
from gettext import gettext as _

from plinth import actions
from plinth.errors import ActionError
from plinth.modules.config import config
from plinth.modules.users.forms import GROUP_CHOICES


class State0Form(forms.ModelForm):
    """Firstboot state 0: Set hostname and create a new user"""
    hostname = forms.CharField(
        label=_('Name of your FreedomBox'),
        help_text=_('For convenience, your FreedomBox needs a name.  It \
should be something short that does not contain spaces or punctuation. \
"Willard" would be a good name while "Freestyle McFreedomBox!!!" would \
not. It must be alphanumeric, start with an alphabet and must not be greater \
than 63 characters in length.'),
        validators=[
            validators.RegexValidator(r'^[a-zA-Z][a-zA-Z0-9]{,62}$',
                                      _('Invalid hostname'))])

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super(State0Form, self).__init__(*args, **kwargs)

    class Meta:
        model = auth.models.User
        fields = ('hostname', 'username', 'password')
        widgets = {
            'password': forms.PasswordInput,
        }
        help_texts = {
            'username':
            _('Choose a username and password to access this web interface. '
              'The password can be changed and other users can be added '
              'later. An LDAP user with administrative privileges (sudo) is '
              'also created.'),
        }

    def save(self, commit=True):
        """Set hostname, create and login the user"""
        config.set_hostname(self.cleaned_data['hostname'])
        user = super(State0Form, self).save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()

            try:
                actions.superuser_run(
                    'ldap',
                    ['create-user', user.get_username()],
                    input=self.cleaned_data['password'].encode())
            except ActionError:
                messages.error(self.request,
                               _('Creating LDAP user failed.'))

            try:
                actions.superuser_run(
                    'ldap',
                    ['add-user-to-group', user.get_username(), 'admin'])
            except ActionError:
                messages.error(self.request,
                               _('Failed to add new user to admin group.'))

            # Create initial Django groups
            for group_choice in GROUP_CHOICES:
                auth.models.Group.objects.get_or_create(name=group_choice[0])

            admin_group = auth.models.Group.objects.get(name='admin')
            admin_group.user_set.add(user)

            self.login_user()

        return user

    def login_user(self):
        """Try to login the user with the credentials provided"""
        try:
            user = auth.authenticate(username=self.request.POST['username'],
                                     password=self.request.POST['password'])
            auth.login(self.request, user)
        except Exception:
            pass
        else:
            message = _('User account created, you are now logged in')
            messages.success(self.request, message)
