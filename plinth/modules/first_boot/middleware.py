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
Django middleware to redirect to firstboot wizard if it has not be run
yet.
"""

from django.http.response import HttpResponseRedirect
from django.urls import reverse
from django.conf import settings
import logging
from operator import itemgetter
from plinth import kvstore, module_loader

LOGGER = logging.getLogger(__name__)

firstboot_steps = []


class FirstBootMiddleware(object):
    """Forward to firstboot page if firstboot isn't finished yet."""

    @staticmethod
    def process_request(request):
        """Handle a request as Django middleware request handler."""
        old_state = kvstore.get_default('firstboot_state', 0)
        state = kvstore.get_default('setup_state', 0)
        if state == 0 and old_state == 10:
            state = 1
            kvstore.set('setup_state', 1)

        user_requests_firstboot = is_firstboot(request.path)
        user_requests_login = request.path.startswith(
            reverse(settings.LOGIN_URL))
        help_index_url = reverse('help:index')
        user_requests_help = request.path.startswith(help_index_url)
        if not user_requests_login and not user_requests_help:
            if state == 1 and user_requests_firstboot:
                return HttpResponseRedirect(reverse('index'))
            elif state == 0 and not user_requests_firstboot:
                url = next_step()
                return HttpResponseRedirect(reverse(url))


def is_firstboot(path):
    """
    Returns whether the path is a firstboot step url
    :param path: path of current url
    :return: true if its a first boot url false otherwise
    """
    steps = get_firstboot_steps()
    for step in steps:
        if reverse(step.get('url')) == path:
            return True

    return False


def get_firstboot_steps():
    """Returns all firstboot steps"""
    steps = []
    modules = module_loader.loaded_modules
    for (module_name, module_object) in modules.items():
        if getattr(module_object, 'first_boot_steps', None):
            for step in module_object.first_boot_steps:
                steps.append(step)

    steps = sorted(steps, key=itemgetter('order'))
    return steps


def next_step():
    """ Returns the next first boot step required to run """
    global firstboot_steps
    if len(firstboot_steps) == 0:
        firstboot_steps = get_firstboot_steps()

    for step in firstboot_steps:
        done = kvstore.get_default(step.get('id'), 0)
        if done == 0:
            return step.get('url')


def mark_step_done(id):
    """
    Marks the status of a first boot step is done
    :param id: id of the firstboot step
    """
    kvstore.set(id, 1)
    global firstboot_steps
    if len(firstboot_steps) == 0:
        firstboot_steps = get_firstboot_steps()

    setup_done = True
    for step in firstboot_steps:
        done = kvstore.get_default(step.get('id'), 0)
        if done == 0:
            setup_done = False
            break

    if setup_done:
        kvstore.set('setup_state', 1)
