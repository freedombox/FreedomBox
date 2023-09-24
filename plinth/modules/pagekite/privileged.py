# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configure PageKite."""

import os

import augeas

from plinth import action_utils
from plinth.actions import privileged
from plinth.modules.pagekite import utils

PATHS = {
    'service_on':
        os.path.join(utils.CONF_PATH, '*', 'service_on', '*'),
    'kitename':
        os.path.join(utils.CONF_PATH, '10_account.rc', 'kitename'),
    'kitesecret':
        os.path.join(utils.CONF_PATH, '10_account.rc', 'kitesecret'),
    'abort_not_configured':
        os.path.join(utils.CONF_PATH, '10_account.rc', 'abort_not_configured'),
    'defaults':
        os.path.join(utils.CONF_PATH, '20_frontends.rc', 'defaults'),
    'frontend':
        os.path.join(utils.CONF_PATH, '20_frontends.rc', 'frontend'),
}


@privileged
def get_config() -> dict[str, object]:
    """Return the current configuration as JSON dictionary."""
    aug = _augeas_load()
    if aug.match(PATHS['abort_not_configured']):
        aug.remove(PATHS['abort_not_configured'])
        aug.save()

    if aug.match(PATHS['defaults']):
        frontend = 'pagekite.net'
    else:
        frontend = aug.get(PATHS['frontend']) or ''

    frontend_parts = frontend.split(':')
    server_domain = frontend_parts[0]
    server_port = frontend_parts[1] if len(frontend_parts) >= 2 else '80'

    status = {
        'kite_name': aug.get(PATHS['kitename']),
        'kite_secret': aug.get(PATHS['kitesecret']),
        'server_domain': server_domain,
        'server_port': server_port,
        'predefined_services': {
            proto: False
            for proto in utils.PREDEFINED_SERVICES
        },
        'custom_services': [],
    }

    # 1. predefined_services: {'http': False, 'ssh': True, 'https': True}
    # 2. custom_services: [{'protocol': 'http', 'secret' 'nono', ..}, [..]}
    for match in aug.match(PATHS['service_on']):
        service = dict([(param, aug.get(os.path.join(match, param)))
                        for param in utils.SERVICE_PARAMS])
        for name, predefined_service in utils.PREDEFINED_SERVICES.items():
            if service == predefined_service['params']:
                status['predefined_services'][name] = True
                break
        else:
            status['custom_services'].append(service)
            if '/' in service['protocol']:
                service['protocol'], service['frontend_port'] = service[
                    'protocol'].split('/')

            service['subdomains'] = service['kitename'].startswith('*.')
            kite_name = status['kite_name']
            protocol = service['protocol']
            if service['subdomains']:
                kite_name = f'*.{kite_name}'

            url = f'{protocol}://{kite_name}'
            if 'frontend_port' in service and service['frontend_port']:
                url = "%s:%s" % (url, service['frontend_port'])

            service['url'] = url

    return status


@privileged
def set_config(frontend: str, kite_name: str, kite_secret: str):
    """Set pagekite kite name, secret and frontend URL."""
    aug = _augeas_load()
    aug.remove(PATHS['abort_not_configured'])

    aug.set(PATHS['kitename'], kite_name)
    aug.set(PATHS['kitesecret'], kite_secret)

    frontend_domain = frontend.split(':')[0]
    if frontend_domain in ('pagekite.net', 'defaults', 'default'):
        aug.set(PATHS['defaults'], '')
        aug.remove(PATHS['frontend'])
    else:
        aug.remove(PATHS['defaults'])
        aug.set(PATHS['frontend'], frontend)

    aug.save()

    for service_name in utils.PREDEFINED_SERVICES.keys():
        service = utils.PREDEFINED_SERVICES[service_name]['params']
        try:
            _add_service(aug, service)
        except RuntimeError:
            pass

    # Immediately after install, pagekite is enabled but not running. Restart
    # based on enabled state instead of try-restart.
    if action_utils.service_is_enabled('pagekite'):
        action_utils.service_restart('pagekite')


@privileged
def remove_service(service: dict[str, str]):
    """Search and remove the service(s) that match all given parameters."""
    aug = _augeas_load()
    service = utils.load_service(service)
    paths = _get_existing_service_paths(aug, service)
    # TODO: theoretically, everything to do here is:
    # [aug.remove(path) for path in paths]
    # but augeas won't let you save the changed files and doesn't say why
    for path in paths:
        filepath = _convert_augeas_path_to_filepath(path)
        service_found = False
        with open(filepath, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            for i, line in enumerate(lines):
                if line.startswith('service_on') and \
                        all(param in line for param in service.values()):
                    lines[i] = ""
                    service_found = True
                    break
        if service_found:
            with open(filepath, 'w', encoding='utf-8') as file:
                file.writelines(lines)
                # abort to only allow deleting one service
                break
    action_utils.service_restart('pagekite')


def _get_existing_service_paths(aug, service, keys=None):
    """Return paths of existing services that match the given service."""
    # construct an augeas query path with patterns like:
    #     */service_on/*[protocol='http']
    path = PATHS['service_on']
    for param in (keys or service.keys()):
        path += "[%s='%s']" % (param, service[param])
    return aug.match(path)


def _add_service(aug, service):
    """Add a new service into configuration."""
    if _get_existing_service_paths(aug, service, ['protocol', 'kitename']):
        msg = "Service with the parameters %s already exists"
        raise RuntimeError(msg % service)

    root = _get_new_service_path(aug, service['protocol'])
    # TODO: after adding a service, augeas fails writing the config;
    # so add the service_on entry manually instead
    path = _convert_augeas_path_to_filepath(root)
    with open(path, 'a', encoding='utf-8') as servicefile:
        line = "\nservice_on = %s\n" % utils.convert_service_to_string(service)
        servicefile.write(line)


@privileged
def add_service(service: dict[str, str]):
    """Add one service."""
    aug = _augeas_load()
    service = utils.load_service(service)
    _add_service(aug, service)
    action_utils.service_try_restart('pagekite')


def _convert_augeas_path_to_filepath(augpath, prefix='/files',
                                     suffix='service_on'):
    """Convert an augeas service_on path to the actual file path."""
    if augpath.startswith(prefix):
        augpath = augpath.replace(prefix, "", 1)

    index = augpath.rfind(suffix)
    if index:
        augpath = augpath[:index]
    return augpath.rstrip('/')


def _get_new_service_path(aug, protocol):
    """Get the augeas path of a new service for a protocol.

    This takes care of existing services using a /service_on/*/ query
    """
    root = utils.get_augeas_servicefile_path(protocol)
    new_index = len(aug.match(root + '/*')) + 1
    return os.path.join(root, str(new_index))


def _augeas_load():
    """Initialize Augeas."""
    aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                        augeas.Augeas.NO_MODL_AUTOLOAD)
    aug.set('/augeas/load/Pagekite/lens', 'Pagekite.lns')
    aug.set('/augeas/load/Pagekite/incl[last() + 1]', '/etc/pagekite.d/*.rc')
    aug.load()
    return aug
