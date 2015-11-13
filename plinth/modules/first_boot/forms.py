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

"""
Forms for first boot module.
"""

from django.contrib import auth
from django.contrib import messages
from django.utils.translation import ugettext as _

from plinth import actions
from plinth.errors import ActionError
from plinth.modules.users.forms import GROUP_CHOICES


class State1Form(auth.forms.UserCreationForm):
    """Firstboot state 1: create a new user."""
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super(State1Form, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        """Create and log the user in."""
        user = super(State1Form, self).save(commit=commit)
        if commit:
            try:
                actions.superuser_run(
                    'ldap',
                    ['create-user', user.get_username()],
                    input=self.cleaned_data['password1'].encode())
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

            self.login_user(self.cleaned_data['username'],
                            self.cleaned_data['password1'])

        return user

    def login_user(self, username, password):
        """Try to login the user with the credentials provided"""
        try:
            user = auth.authenticate(username=username, password=password)
            auth.login(self.request, user)
        except Exception:
            pass
        else:
            message = _('User account created, you are now logged in')
            messages.success(self.request, message)
