# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configure Home Assistant."""

import contextlib
import functools
import json
import pathlib
import time
import traceback
from dataclasses import dataclass

import yaml

from freedombox import action_utils
from freedombox.actions import privileged

_old_settings_file = pathlib.Path(
    '/var/lib/home-assistant-freedombox/config/configuration.yaml')
_settings_file = pathlib.Path(
    '/var/lib/home-assistant-freedombox/config/.storage/http')


@dataclass
class YAMLUnknownTag:
    """Object used to represent an unknown tag in YAML."""
    tag: str
    value: str


class YAMLLoader(yaml.SafeLoader):
    """Custom YAML loader to handle !include etc. tags."""
    pass


def yaml_unknown_constructor(loader, node, tag):
    """Create an object when a unknown tag is encountered."""
    value = loader.construct_scalar(node)
    return YAMLUnknownTag(tag, value)


class YAMLDumper(yaml.Dumper):
    """Custom YAML dumper to handle !include etc. tags."""
    pass


def yaml_unknown_representor(dumper, data):
    """Dump original tag from an object representing an unknown tag."""
    return dumper.represent_scalar(data.tag, data.value)


def yaml_add_handlers():
    """Add special handlers to YAML loader and dumper."""
    tags = [
        '!include', '!env_var', '!secret', '!include_dir_list',
        '!include_dir_merge_list', '!include_dir_named',
        '!include_dir_merge_named', '!input'
    ]
    for tag in tags:
        YAMLLoader.add_constructor(
            tag, functools.partial(yaml_unknown_constructor, tag=tag))

    YAMLDumper.add_representer(YAMLUnknownTag, yaml_unknown_representor)


yaml_add_handlers()


@privileged
def setup(old_version: int) -> None:
    """Setup basic Home Assistant configuration."""
    pathlib.Path('/var/lib/home-assistant-freedombox/').chmod(0o700)

    if old_version == 1:
        _migrate_old_configuration()

    _wait_for_configuration_file(_settings_file)

    with _ensure_stopped():
        try:
            settings = _read_settings()
            version = settings.get('version', 0)
            if version != 2:
                raise Exception(
                    f'Configuration format not understood: {version}.')

            settings.setdefault('data', {})
            settings['data'].setdefault('stable', {})
            settings['data']['stable']['server_host'] = '127.0.0.1'
            settings['data']['stable']['use_x_forwarded_for'] = True
            settings['data']['stable']['trusted_proxies'] = ['127.0.0.1']
            _write_settings(settings)
        except Exception as exception:
            raise Exception(
                traceback.format_tb(exception.__traceback__) +
                [_settings_file.read_text()])


def _wait_for_configuration_file(settings_file: pathlib.Path) -> None:
    """Wait until the Home Assistant daemon creates a configuration file."""
    start_time = time.time()
    while time.time() < start_time + 300:
        if settings_file.exists():
            break

        time.sleep(1)


def _read_settings() -> dict:
    """Load internal storage for HTTP configuration."""
    with _settings_file.open('rb') as file_handle:
        return json.load(file_handle)


def _write_settings(settings: dict):
    """Write HTTP configuration into internal storage."""
    with _settings_file.open('w') as file_handle:
        return json.dump(settings, file_handle, indent=2)


def _migrate_old_configuration():
    """Migrate old configuration file."""
    _wait_for_configuration_file(_old_settings_file)
    try:
        settings = _read_old_settings()
        if 'http' in settings:
            del settings['http']

        _write_old_settings(settings)
    except Exception as exception:
        print('Unable to upgrade old configuration file.', exception)


def _read_old_settings() -> dict:
    """Load settings as dictionary from YAML config file."""
    with _old_settings_file.open('rb') as file_handle:
        return yaml.load(file_handle, Loader=YAMLLoader)


def _write_old_settings(settings: dict):
    """Write settings from dictionary to YAML config file."""
    with _old_settings_file.open('w', encoding='utf-8') as file_handle:
        yaml.dump(settings, file_handle, Dumper=YAMLDumper)


@contextlib.contextmanager
def _ensure_stopped():
    """Ensure that the service is stopped."""
    name = 'home-assistant-freedombox'

    starting_state = action_utils.service_is_running(name)
    if starting_state:
        action_utils.service_disable(name)

    try:
        yield starting_state
    finally:
        if starting_state:
            action_utils.service_enable(name)
