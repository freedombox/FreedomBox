#!/usr/bin/python3
# -*- mode: python -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Cleanup actions to be run when a vagrant box is destroyed.
"""

import os

# Drop Plinth database
try:
    os.remove('data/var/lib/plinth/plinth.sqlite3')
except OSError:
    pass
