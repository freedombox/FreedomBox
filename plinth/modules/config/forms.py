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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

"""
Forms for basic system configuration
"""


from django import forms
from django.utils.translation import ugettext as _, ugettext_lazy
from django.core import validators
from django.core.exceptions import ValidationError

from plinth import cfg
from plinth.utils import format_lazy

import logging
import re

logger = logging.getLogger(__name__)

HOSTNAME_REGEX = r'^[a-zA-Z0-9]([-a-zA-Z0-9]{,61}[a-zA-Z0-9])?$'


class TrimmedCharField(forms.CharField):
    """Trim the contents of a CharField"""
    def clean(self, value):
        """Clean and validate the field value"""
        if value:
            value = value.strip()

        return super(TrimmedCharField, self).clean(value)


def domain_label_validator(domainname):
    """Validate domain name labels."""
    for label in domainname.split('.'):
        if not re.match(HOSTNAME_REGEX, label):
            raise ValidationError(_('Invalid domain name'))


class ConfigurationForm(forms.Form):
    """Main system configuration form"""
    # See:
    # https://tools.ietf.org/html/rfc952
    # https://tools.ietf.org/html/rfc1035#section-2.3.1
    # https://tools.ietf.org/html/rfc1123#section-2
    # https://tools.ietf.org/html/rfc2181#section-11
    hostname = TrimmedCharField(
        label=ugettext_lazy('Hostname'),
        help_text=format_lazy(ugettext_lazy(
            'Hostname is the local name by which other devices on the local '
            'network can reach your {box_name}.  It must start and end with '
            'an alphabet or a digit and have as interior characters only '
            'alphabets, digits and hyphens.  Total length must be 63 '
            'characters or less.'), box_name=ugettext_lazy(cfg.box_name)),
        validators=[
            validators.RegexValidator(
                HOSTNAME_REGEX,
                ugettext_lazy('Invalid hostname'))])

    domainname = TrimmedCharField(
        label=ugettext_lazy('Domain Name'),
        help_text=format_lazy(ugettext_lazy(
            'Domain name is the global name by which other devices on the '
            'Internet can reach your {box_name}.  It must consist of labels '
            'separated by dots.  Each label must start and end with an '
            'alphabet or a digit and have as interior characters only '
            'alphabets, digits and hyphens.  Length of each label must be 63 '
            'characters or less.  Total length of domain name must be 253 '
            'characters or less.'), box_name=ugettext_lazy(cfg.box_name)),
        required=False,
        validators=[
            validators.RegexValidator(
                r'^[a-zA-Z0-9]([-a-zA-Z0-9.]{,251}[a-zA-Z0-9])?$',
                ugettext_lazy('Invalid domain name')),
            domain_label_validator])
