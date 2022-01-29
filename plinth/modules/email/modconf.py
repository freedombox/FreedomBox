# SPDX-License-Identifier: AGPL-3.0-or-later
"""Generic config modifying utilities"""

import contextlib
import io
import re

from . import interproc


class ConfigInjector:
    def __init__(self, match, generate):
        self.re_pattern = re.compile(match)
        self.boundary_fmt = generate + '\n'

    def do_file_des(self, template, config, scratch):
        """Write modified config to the `scratch` stream"""
        if not isinstance(template, io.TextIOBase):
            raise TypeError('Not a text IO stream: template')
        self._inject_config3(template, config, scratch)

    def _inject_config3(self, template, config, scratch):
        # Copy the original config up to header line
        for line in config:
            match = self.re_pattern.match(line.strip())
            if match and match.group(1) == 'BEGIN':
                break
            scratch.write(line)
            if not line.endswith('\n'):  # in case no new line was at the eof
                scratch.write('\n')

        # Write header line
        scratch.write(self.boundary_fmt.format('BEGIN'))
        # Write template to scratch
        for line in template:
            scratch.write(line)
            # in case no new line was at the eof
            if not line.endswith('\n'):
                scratch.write('\n')
        # Write footer line
        scratch.write(self.boundary_fmt.format('END'))

        # Find the trailer line in config
        for line in config:
            match = self.re_pattern.match(line.strip())
            if match and match.group(1) == 'END':
                break

        # Copy the original
        for line in config:
            scratch.write(line)  # keep original file ending style

    def do_template_file(self, template_path, config_path):
        with open(template_path, 'r') as template:
            with self._open_config(config_path) as (config, scratch):
                self._inject_config3(template, config, scratch)

    def do_template_string(self, template_string, config_path):
        with self._open_config(config_path) as (config, scratch):
            self._inject_config3([template_string], config, scratch)

    @contextlib.contextmanager
    def _open_config(self, config_path):
        with open(config_path, 'a+') as config:
            with interproc.atomically_rewrite(config_path) as scratch:
                config.seek(0)
                yield config, scratch

    def has_header_line(self, config_path):
        with open(config_path, 'r') as config_fd:
            return self._has_header_line(config_fd)

    def _has_header_line(self, config_fd):
        for line in config_fd:
            match = self.re_pattern.match(line.strip())
            if match and match.group(1) == 'BEGIN':
                return True
        return False
