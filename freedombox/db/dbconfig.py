# SPDX-License-Identifier: AGPL-3.0-or-later
"""Utilities for parsing dbconfig-common files with Augeas."""

import pathlib

import augeas


def get_credentials(dbconfig_path: str) -> dict[str, str]:
    """Parse dbconfig-common file with Augeas Shellvars lens."""
    if not pathlib.Path(dbconfig_path).is_file():
        raise FileNotFoundError(f'DB config not found: {dbconfig_path}')

    aug = _load_augeas(dbconfig_path)

    required = ['dbc_dbuser', 'dbc_dbpass', 'dbc_dbname']
    credentials = {}
    for key in required + ['dbc_dbserver']:
        credentials[key] = aug.get(key).strip('\'"')

    if not all(credentials.get(key) for key in required):
        raise ValueError('Missing required dbconfig-common credentials')

    return {
        'user': credentials['dbc_dbuser'],
        'password': credentials['dbc_dbpass'],
        'database': credentials['dbc_dbname'],
        'host': credentials['dbc_dbserver'] or 'localhost'
    }


def _load_augeas(config_path: str):
    """Initialize Augeas."""
    aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                        augeas.Augeas.NO_MODL_AUTOLOAD)
    pathstr = str(config_path)
    aug.transform('Shellvars', pathstr)
    aug.set('/augeas/context', f'/files{pathstr}')
    aug.load()
    return aug
