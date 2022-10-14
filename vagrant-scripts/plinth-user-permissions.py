#!/usr/bin/python3
# -*- mode: python -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Set required permissions for user "plinth" to run plinth in dev setup."""

import pathlib

content = '''
Cmnd_Alias FREEDOMBOX_ACTION_DEV = /usr/share/plinth/actions/actions, /vagrant/actions/actions
Defaults!FREEDOMBOX_ACTION_DEV closefrom_override
plinth ALL=(ALL:ALL) NOPASSWD:SETENV : FREEDOMBOX_ACTION_DEV
fbx    ALL=(ALL:ALL) NOPASSWD : ALL
'''

sudoers_file = pathlib.Path('/etc/sudoers.d/01-freedombox-development')
sudoers_file.write_text(content)
