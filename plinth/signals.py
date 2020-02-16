# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Django signals emitted within FreedomBox.
"""

from django.dispatch import Signal

pre_module_loading = Signal()
post_module_loading = Signal()
post_setup = Signal(providing_args=['module_name'])
pre_hostname_change = Signal(providing_args=['old_hostname', 'new_hostname'])
post_hostname_change = Signal(providing_args=['old_hostname', 'new_hostname'])
domain_added = Signal(
    providing_args=['domain_type', 'name', 'description', 'services'])
domain_removed = Signal(providing_args=['domain_type', 'name'])
