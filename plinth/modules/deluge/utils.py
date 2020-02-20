# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Utilities for editing configuration files of Deluge.
"""

import copy
import json
import os
import pathlib
import re
import shutil
import tempfile

_JSON_FORMAT = {'indent': 4, 'sort_keys': True, 'ensure_ascii': False}


class Config:
    """Read or edit a Deluge configuration file."""
    def __init__(self, file_name):
        """Initialize the configuration object."""
        self.file_name = file_name
        self.file = pathlib.Path(self.file_name)
        self._version = None
        self.content = None
        self._original_content = None

    def load(self):
        """Parse the configuration file into memory."""
        text = self.file.read_text()
        matches = re.match(r'^({[^}]*})(.*)$', text, re.DOTALL)
        if not matches:
            raise Exception('Unexpected file format.')

        try:
            self._version = json.loads(matches.group(1))
            self.content = json.loads(matches.group(2))
        except json.decoder.JSONDecoderError:
            raise Exception('Unable to parse JSON in file.')

        if self._version['format'] != 1:
            raise Exception('Version of the config file not understood')

        self._original_content = copy.deepcopy(self.content)

    def save(self):
        """Atomically save the modified configuration to file."""
        if self.content == self._original_content:
            return

        with tempfile.NamedTemporaryFile(dir=self.file.parent,
                                         delete=False) as new_file:
            new_file.write(json.dumps(self._version, **_JSON_FORMAT).encode())
            new_file.write(json.dumps(self.content, **_JSON_FORMAT).encode())
            new_file.flush()
            os.fsync(new_file.fileno())

        new_file_path = pathlib.Path(new_file.name)
        new_file_path.chmod(0o600)
        try:
            shutil.chown(str(new_file_path), 'debian-deluged',
                         'debian-deluged')
        except (PermissionError, LookupError):
            pass  # Not running as root, or deluge is not installed

        new_file_path.rename(self.file)

    def __enter__(self):
        """Enter the context."""
        self.load()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Exit the context."""
        self.save()
