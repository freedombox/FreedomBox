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
Plinth module to manage users
"""

from django.db.models.signals import post_delete
from django.contrib.auth.models import User
from gettext import gettext as _

from plinth import cfg
from plinth import actions

__all__ = ['init']

depends = ['plinth.modules.system']


def init():
    """Intialize the user module."""
    menu = cfg.main_menu.get('system:index')
    menu.add_urlname(_('Users and Groups'), 'glyphicon-user', 'users:index',
                     15)

    post_delete.connect(delete_posix_user)


def delete_posix_user(sender, instance=None, **kwargs):
    try:
        instance
    except User.DoesNotExist:
        pass
    else:
        actions.superuser_run('delete-user', [instance.username])
