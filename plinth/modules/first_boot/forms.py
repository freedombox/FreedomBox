#
# This file is part of FreedomBox.
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
from django.utils.translation import ugettext_lazy as _

from plinth.modules import first_boot


class FirstbootWizardSecretForm(forms.Form):
    """Form to collect and validate the first boot wizard secret."""
    secret = forms.CharField(
        label='', help_text=_(
            'Enter the secret generated during FreedomBox installation. '
            'This secret can also be obtained from the file '
            '/var/lib/plinth/firstboot-wizard-secret'), required=False,
        widget=forms.PasswordInput(attrs={'placeholder': _('Secret')}))

    def validate_secret(self, secret):
        """Match the secret provided by the user with the one
        generated during installation.
        """
        secret_file_path = first_boot.get_secret_file_path()
        with open(secret_file_path) as secret_file:
            if secret != secret_file.read().strip():
                self.add_error('secret', 'Invalid secret')

    def clean(self):
        """Override clean to add form validation logic."""
        cleaned_data = super().clean()
        if first_boot.firstboot_wizard_secret_exists():
            self.validate_secret(cleaned_data.get("secret"))
        return cleaned_data
