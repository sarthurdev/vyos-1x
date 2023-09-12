#!/usr/bin/env python3
#
# Copyright (C) 2023 VyOS maintainers and contributors
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

from sys import argv
from sys import exit
from time import sleep

from vyos.config import Config
from vyos.configdict import get_interface_dict
from vyos.ifconfig import VTunIf
#from vyos.utils.commit import commit_in_progress

interface = argv[1]

#while commit_in_progress():
#    sleep(1)

conf = Config()
_, openvpn = get_interface_dict(conf, ['interfaces', 'openvpn'], interface)

# Update the config
o = VTunIf(interface)
o.update(openvpn)
