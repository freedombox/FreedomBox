#!/usr/bin/python3
# -*- mode: python -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Set required permissions for user "plinth" to run plinth in the development
environment.
"""

import augeas

sudoers_file = '/etc/sudoers.d/plinth'
aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                    augeas.Augeas.NO_MODL_AUTOLOAD)

# lens for shell-script config file
aug.set('/augeas/load/Shellvars/lens', 'Sudoers.lns')
aug.set('/augeas/load/Shellvars/incl[last() + 1]', sudoers_file)
aug.load()

aug.set('/files{}/spec[1]/host_group/command[2]'.format(sudoers_file),
        '/vagrant/actions/*')
aug.set('/files{}/spec[1]/host_group/command[1]/tag[2]'.format(sudoers_file),
        'SETENV')
aug.save()
