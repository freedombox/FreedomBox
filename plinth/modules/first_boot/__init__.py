# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for first boot wizard.
"""

import operator
import os
import sys

from django.urls import reverse
from django.utils.translation import gettext_noop

from plinth import app as app_module
from plinth import cfg
from plinth.signals import post_setup

first_boot_steps = [
    {
        'id': 'firstboot_welcome',
        'url': 'first_boot:welcome',
        'order': 0
    },
]

_all_first_boot_steps = None

_is_completed = None


class FirstBootApp(app_module.App):
    """FreedomBox app for First Boot."""

    app_id = 'first_boot'

    _version = 1

    def __init__(self) -> None:
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(app_id=self.app_id, version=self._version,
                               is_essential=True)
        self.add(info)

    def post_init(self):
        """Perform post initialization operations."""
        post_setup.connect(_clear_first_boot_steps)

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)

        if not old_version:
            self._show_next_steps_notification()

        self.enable()

    def _show_next_steps_notification(self):
        """After first setup, show notification for next steps."""
        from plinth.notification import Notification
        title = gettext_noop('Setup complete! Next steps:')
        message = gettext_noop(
            'Initial setup has been completed. Perform the next steps to make '
            'your {box_name} operational.')
        data = {
            'app_name': 'translate:' + gettext_noop('Next steps'),
            'app_icon': 'fa-arrow-right',
            'box_name': 'translate:' + cfg.box_name
        }
        actions = [{
            'type': 'link',
            'class': 'primary',
            'text': gettext_noop('See next steps'),
            'url': 'first_boot:complete'
        }, {
            'type': 'dismiss'
        }]
        Notification.update_or_create(id='first-boot-complete',
                                      app_id='first_boot', severity='info',
                                      title=title, message=message,
                                      actions=actions, data=data,
                                      group='admin', dismissed=False)


def _clear_first_boot_steps(sender, module_name, **kwargs):
    """Flush the cache of first boot steps so it is recreated."""
    global _all_first_boot_steps
    _all_first_boot_steps = None


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
    for app in app_module.App.list():
        module = sys.modules[app.__module__]
        if getattr(module, 'first_boot_steps', None):
            if not app.needs_setup():
                steps.extend(module.first_boot_steps)

    _all_first_boot_steps = sorted(steps, key=operator.itemgetter('order'))
    return _all_first_boot_steps


def next_step():
    """Return the resolved next first boot step URL required to go to.

    If there are no more step remaining, return 'complete' page.
    """
    return next_step_or_none() or 'first_boot:complete'


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


def get_secret_file_path():
    """Returns the path to the first boot wizard secret file."""
    return os.path.join(cfg.data_dir, 'firstboot-wizard-secret')


def firstboot_wizard_secret_exists():
    """Return whether a firstboot wizard secret exists."""
    secret_file = get_secret_file_path()
    return os.path.exists(secret_file) and os.path.getsize(secret_file) > 0
