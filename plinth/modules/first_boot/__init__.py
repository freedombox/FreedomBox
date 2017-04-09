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
Plinth module for first boot wizard
"""

from django.urls import reverse
import operator

from plinth import module_loader

version = 1

is_essential = True

first_boot_steps = [
    {
        'id': 'firstboot_welcome',
        'url': 'first_boot:welcome',
        'order': 0
    },
    {
        # TODO: Rename this, or merge with 'firstboot_completed'.
        'id': 'firstboot_complete',
        'url': 'first_boot:complete',
        'order': 10
    }
]

_all_first_boot_steps = None

_is_completed = None


def is_firstboot_url(path):
    """Return whether a path is a firstboot step URL.

    :param path: path of url to be checked
    :return: true if its a first boot URL false otherwise
    """
    for step in _get_steps():
        if path.startswith(reverse(step['url'])):
            return True

    return False


def _get_steps():
    """Return list of all firstboot steps."""
    global _all_first_boot_steps
    if _all_first_boot_steps is not None:
        return _all_first_boot_steps

    steps = []
    modules = module_loader.loaded_modules
    for module_object in modules.values():
        if getattr(module_object, 'first_boot_steps', None):
            if module_object.setup_helper.get_state() != 'needs-setup':
                steps.extend(module_object.first_boot_steps)

    _all_first_boot_steps = sorted(steps, key=operator.itemgetter('order'))
    return _all_first_boot_steps


def next_step():
    """Return the resolved next first boot step URL required to go to.

    If there are no more step remaining, return index page.
    """
    return next_step_or_none() or 'index'


def next_step_or_none():
    """Return the next first boot step required to run.

    If there are no more step remaining, return None.
    """
    from plinth import kvstore

    for step in _get_steps():
        done = kvstore.get_default(step['id'], 0)
        if not done:
            return step.get('url')


def mark_step_done(id):
    """Marks the status of a first boot step as done.

    :param id: id of the firstboot step
    """
    from plinth import kvstore

    kvstore.set(id, 1)
    if not next_step_or_none():
        set_completed()


def is_completed():
    """Return whether first boot process is completed."""
    from plinth import kvstore

    global _is_completed
    if _is_completed is None:
        _is_completed = kvstore.get_default('firstboot_completed', 0)

    return bool(_is_completed)


def set_completed():
    """Set the first boot process as completed."""
    from plinth import kvstore

    global _is_completed
    _is_completed = True
    kvstore.set('firstboot_completed', 1)
