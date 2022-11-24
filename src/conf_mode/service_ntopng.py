#!/usr/bin/env python3
#
# Copyright (C) 2022 VyOS maintainers and contributors
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 or later as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os

from sys import exit

from vyos.config import Config
from vyos.configdict import dict_merge
from vyos.configverify import verify_interface_exists
from vyos.template import render
from vyos.util import call
from vyos.xml import defaults
from vyos import ConfigError
from vyos import airbag
airbag.enable()

ntopng_conf = r'/run/ntopng/ntopng.conf'
ntopng_service = 'ntopng.service'
redis_service = 'redis-server.service'

def get_config(config=None):
    if config:
        conf = config
    else:
        conf = Config()
    base = ['service', 'ntopng']
    if not conf.exists(base):
        return None

    ntopng = conf.get_config_dict(base, key_mangling=('-', '_'),
                                      get_first_key=True)

    default_values = defaults(base)
    ntopng = dict_merge(default_values, ntopng)

    return ntopng

def verify(ntopng):
    if not ntopng:
        return None

    if 'interface' not in ntopng:
        raise ConfigError('At least one interface must be defined')

    for ifname in ntopng['interface']:
        verify_interface_exists(ifname)

    if 'listen_address' not in ntopng:
        raise ConfigError('listen-address must be defined')

    if 'port' not in ntopng:
        raise ConfigError('port must be defined')

    return None

def generate(ntopng):
    if not ntopng:
        return None

    render(ntopng_conf, 'ntopng/ntopng.conf.j2', ntopng)
    return None

def apply(ntopng):
    if not ntopng:
        call(f'systemctl stop {ntopng_service}')
        call(f'systemctl stop {redis_service}')
        os.unlink(ntopng_conf)
        return None

    call(f'systemctl reload-or-restart {redis_service}')
    call(f'systemctl restart {ntopng_service}')

if __name__ == '__main__':
    try:
        c = get_config()
        verify(c)
        generate(c)
        apply(c)
    except ConfigError as e:
        print(e)
        exit(1)
