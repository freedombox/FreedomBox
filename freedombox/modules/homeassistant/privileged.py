# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configure Home Assistant."""

import functools
import pathlib
import time
import traceback
from dataclasses import dataclass

import yaml

from plinth.actions import privileged

_settings_file = pathlib.Path(
    '/var/lib/home-assistant-freedombox/config/configuration.yaml')


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
def setup() -> None:
    """Setup basic Home Assistant configuration."""
    pathlib.Path('/var/lib/home-assistant-freedombox/').chmod(0o700)

    try:
        _wait_for_configuration_file()

        settings = _read_settings()
        if 'http' not in settings:
            settings['http'] = {}

        settings['http']['server_host'] = '127.0.0.1'
        settings['http']['use_x_forwarded_for'] = True
        settings['http']['trusted_proxies'] = '127.0.0.1'
        _write_settings(settings)
    except Exception as exception:
        raise Exception(
            traceback.format_tb(exception.__traceback__) +
            [_settings_file.read_text()])


def _wait_for_configuration_file() -> None:
    """Wait until the Home Assistant daemon creates a configuration file."""
    start_time = time.time()
    while time.time() < start_time + 300:
        if _settings_file.exists():
            break

        time.sleep(1)


def _read_settings() -> dict:
    """Load settings as dictionary from YAML config file."""
    with _settings_file.open('rb') as settings_file:
        return yaml.load(settings_file, Loader=YAMLLoader)


def _write_settings(settings: dict):
    """Write settings from dictionary to YAML config file."""
    with _settings_file.open('w', encoding='utf-8') as settings_file:
        yaml.dump(settings, settings_file, Dumper=YAMLDumper)
