# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Various helpers for the I2P app.
"""

import os
import re
from collections import OrderedDict

import augeas

I2P_CONF_DIR = '/var/lib/i2p/i2p-config'
FILE_TUNNEL_CONF = os.path.join(I2P_CONF_DIR, 'i2ptunnel.config')
TUNNEL_IDX_REGEX = re.compile(r'tunnel.(\d+).name$')
I2P_ROUTER_CONF = os.path.join(I2P_CONF_DIR, 'router.config')


class TunnelEditor():
    """Helper to edit I2P tunnel configuration file using augeas.

    :type aug: augeas.Augeas

    """
    def __init__(self, conf_filename=None, idx=None):
        self.conf_filename = conf_filename or FILE_TUNNEL_CONF
        self.idx = idx
        self.aug = None

    @property
    def lines(self):
        """Return lines from configuration file."""
        if self.aug:
            return self.aug.match('/files{}/*'.format(self.conf_filename))

        return []

    def read_conf(self):
        """Load an instance of Augeaus for processing APT configuration.

        Chainable method.

        """
        self.aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                                 augeas.Augeas.NO_MODL_AUTOLOAD)
        self.aug.set('/augeas/load/Properties/lens', 'Properties.lns')
        self.aug.set('/augeas/load/Properties/incl[last() + 1]',
                     self.conf_filename)
        self.aug.load()

        return self

    def write_conf(self):
        """Write changes to the configuration file to disk.

        Chainable method.

        """
        self.aug.save()
        return self

    def set_tunnel_idx(self, name):
        """Finds the index of the tunnel with the given name.

        Chainable method.

        :type name: basestring

        """
        for prop in self.aug.match('/files{}/*'.format(self.conf_filename)):
            match = TUNNEL_IDX_REGEX.search(prop)
            if match and self.aug.get(prop) == name:
                self.idx = int(match.group(1))
                return self

        raise ValueError('No tunnel called {}'.format(name))

    def calc_prop_path(self, tunnel_prop):
        """Calculates the property name as found in the properties files.

        :type tunnel_prop: str
        :rtype: basestring

        """
        calced_prop_path = \
            '/files{filepath}/tunnel.{idx}.{tunnel_prop}'.format(
                idx=self.idx,
                tunnel_prop=tunnel_prop,
                filepath=self.conf_filename)
        return calced_prop_path

    def set_tunnel_prop(self, tunnel_prop, value):
        """Updates a tunnel's property.

        The idx has to be set and the property has to exist in the config file
        and belong to the tunnel's properties.

        See calc_prop_path.

        Chainable method.

        :param tunnel_prop:
        :type tunnel_prop: str
        :param value:
        :type value: basestring | int
        :return:
        :rtype:

        """
        if self.idx is None:
            raise ValueError(
                'Please init the tunnel index before calling this method')

        calc_prop_path = self.calc_prop_path(tunnel_prop)
        self.aug.set(calc_prop_path, value)
        return self

    def __getitem__(self, tunnel_prop):
        ret = self.aug.get(self.calc_prop_path(tunnel_prop))
        if ret is None:
            raise KeyError('Unknown property {}'.format(tunnel_prop))

        return ret

    def __setitem__(self, tunnel_prop, value):
        self.aug.set(self.calc_prop_path(tunnel_prop), value)


class RouterEditor():
    """Helper to edit I2P router configuration file using augeas.

    :type aug: augeas.Augeas

    """

    FAVORITE_PROP = 'routerconsole.favorites'
    FAVORITE_TUPLE_SIZE = 4

    def __init__(self, filename=None):
        self.conf_filename = filename or I2P_ROUTER_CONF
        self.aug = None

    def read_conf(self):
        """Load an instance of Augeaus for processing APT configuration.

        Chainable method.

        """
        self.aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                                 augeas.Augeas.NO_MODL_AUTOLOAD)
        self.aug.set('/augeas/load/Properties/lens', 'Properties.lns')
        self.aug.set('/augeas/load/Properties/incl[last() + 1]',
                     self.conf_filename)
        self.aug.load()
        return self

    def write_conf(self):
        """Write changes to the configuration file to disk.

        Chainable method.

        """
        self.aug.save()
        return self

    @property
    def favorite_property(self):
        """Return the favourites property from configuration file."""
        return '/files{filename}/{prop}'.format(filename=self.conf_filename,
                                                prop=self.FAVORITE_PROP)

    def add_favorite(self, name, url, description=None, icon=None):
        """Add a favorite to the router configuration file.

        Favorites are in a single string and separated by ','. none of the
        incoming params can therefore use commas. I2P replaces the commas by
        dots.

        That's ok for the name and description, but not for the url and icon.

        :type name: basestring
        :type url: basestring
        :type description: basestring
        :type icon: basestring

        """
        if not description:
            description = ''

        if not icon:
            icon = '/themes/console/images/eepsite.png'

        if ',' in url:
            raise ValueError('URL cannot contain commas')

        if ',' in icon:
            raise ValueError('Icon cannot contain commas')

        name = name.replace(',', '.')
        description = description.replace(',', '.')

        prop = self.favorite_property
        favorites = self.aug.get(prop) or ''
        new_favorite = '{name},{description},{url},{icon},'.format(
            name=name, description=description, url=url, icon=icon)
        self.aug.set(prop, favorites + new_favorite)
        return self

    def get_favorites(self):
        """Return list of favorites."""
        favs_string = self.aug.get(self.favorite_property) or ''
        favs_split = favs_string.split(',')

        # There's a trailing comma --> 1 extra
        favs_len = len(favs_split)
        if favs_len > 0:
            favs_split = favs_split[:-1]
            favs_len = len(favs_split)

        if favs_len % self.FAVORITE_TUPLE_SIZE:
            raise SyntaxError("Invalid number of fields in favorite line")

        favs = OrderedDict()
        for index in range(0, favs_len, self.FAVORITE_TUPLE_SIZE):
            next_index = index + self.FAVORITE_TUPLE_SIZE
            name, description, url, icon = favs_split[index:next_index]
            favs[url] = {
                'name': name,
                'description': description,
                'icon': icon
            }

        return favs
