# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Django signals emitted within FreedomBox.
"""

from django.dispatch import Signal

# Arguments: -
pre_module_loading = Signal()

# Arguments: -
post_module_loading = Signal()

# Arguments: module_name
post_setup = Signal()

# Arguments: old_hostname, new_hostname
pre_hostname_change = Signal()

# Arguments: old_hostname, new_hostname
post_hostname_change = Signal()

# Arguments: domain_type, name, description, services
domain_added = Signal()

# Arguments: domain_type, name
domain_removed = Signal()
