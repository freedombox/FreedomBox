# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Template tags for first boot module.
"""

from django import template

from plinth.modules import first_boot

register = template.Library()


@register.simple_tag
def firstboot_is_completed():
    """Return whether firstboot process is completed."""
    return first_boot.is_completed()
