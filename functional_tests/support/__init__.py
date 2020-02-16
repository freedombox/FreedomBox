# SPDX-License-Identifier: AGPL-3.0-or-later

import configparser
import os
import pathlib

config = configparser.ConfigParser()
config.read(pathlib.Path(__file__).parent.with_name('config.ini'))

config['DEFAULT']['url'] = os.environ.get('FREEDOMBOX_URL',
                                          config['DEFAULT']['url'])
config['DEFAULT']['samba_port'] = os.environ.get('FREEDOMBOX_SAMBA_PORT',
                                          config['DEFAULT']['samba_port'])
