#!/usr/bin/python3
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
Configuration helper for Minetest.
"""

import os
import sys
import time
from urllib import request, error

import argparse
import augeas

from plinth import action_utils

CONFIG = '/etc/minetest/minetest.conf'
AUG_PATH = '/files' + CONFIG + '/.anon/'


def parse_arguments():
    """Return parsed command line arguments as dictionary."""
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='subcommand', help='Sub command')

    minetest_mod_advspawning = subparsers.add_parser('minetest-mod \
                                                     -advspawning', help='Configure minetest \
                                                     -mod-advspawning')
    minetest_mod_advspawning.add_argument('--domain', help='Domain name')

    minetest_mod_animalmaterials = subparsers.add_parser(
                                          'minetest-mod-animalmaterials',
                                          help='Remove domain name')
    minetest_mod_animalmaterials.add_argument('--domain', help='Domain name')

    minetest_mod_animals = subparsers.add_parser('minetest-mod \
                                                     -animals', help='Configure minetest \
                                                     -mod-animals')
    minetest_mod_animals.add_argument('--domain', help='Domain name')

    minetest_mod_mesecons = subparsers.add_parser('minetest-mod \
                                                     -mesecons', help='Configure minetest \
                                                     -mod-mesecons')
    minetest_mod_mesecons.add_argument('--domain', help='Domain name')

    minetest_mod_mobf_core = subparsers.add_parser('minetest-mod \
                                                     -mobf-core', help='Configure minetest \
                                                     -mod-mobf-core')
    minetest_mod_mobf_core.add_argument('--domain', help='Domain name')

    minetest_mod_mobf_trap = subparsers.add_parser('minetest-mod \
                                                     -mobf-trap', help='Configure minetest \
                                                     -mod-mobf-trap')
    minetest_mod_mobf_trap.add_argument('--domain', help='Domain name')

    minetest_mod_moreblocks = subparsers.add_parser('minetest-mod \
                                                     -moreblocks', help='Configure minetest \
                                                     -mod-moreblocks')
    minetest_mod_moreblocks.add_argument('--domain', help='Domain name')

    minetest_mod_nether = subparsers.add_parser('minetest-mod \
                                                     -nether', help='Configure minetest \
                                                     -mod-nether')
    minetest_mod_nether.add_argument('--domain', help='Domain name')

    minetest_mod_torches = subparsers.add_parser('minetest-mod \
                                                     -torches', help='Configure minetest \
                                                     -mod-torches')
    minetest_mod_torches.add_argument('--domain', help='Domain name')

    return parser.parse_args()
