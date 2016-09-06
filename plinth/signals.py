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
Plinth signals
"""

from django.dispatch import Signal


service_enabled = Signal(providing_args=['service_id', 'enabled'])
pre_module_loading = Signal()
post_module_loading = Signal()
pre_hostname_change = Signal(providing_args=['old_hostname', 'new_hostname'])
post_hostname_change = Signal(providing_args=['old_hostname', 'new_hostname'])
domainname_change = Signal(providing_args=['old_domainname', 'new_domainname'])
domain_added = Signal(providing_args=['domain_type', 'name', 'description',
                                      'services'])
domain_removed = Signal(providing_args=['domain_type', 'name'])
letsencrypt_cert_obtained = Signal(providing_args=['domain'])
letsencrypt_cert_revoked = Signal(providing_args=['domain'])
