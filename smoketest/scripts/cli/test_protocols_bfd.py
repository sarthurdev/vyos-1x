#!/usr/bin/env python3
#
# Copyright (C) 2021 VyOS maintainers and contributors
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

import unittest

from base_vyostest_shim import VyOSUnitTestSHIM
from vyos.configsession import ConfigSession
from vyos.configsession import ConfigSessionError
from vyos.util import process_named_running

PROCESS_NAME = 'bfdd'
base_path = ['protocols', 'bfd']

dum_if = 'dum1001'
peers = {
    '192.0.2.10' : {
        'intv_rx'    : '500',
        'intv_tx'    : '600',
        'multihop'   : '',
        'source_addr': '192.0.2.254',
        },
    '192.0.2.20' : {
        'echo_mode'  : '',
        'intv_echo'  : '100',
        'intv_mult'  : '100',
        'intv_rx'    : '222',
        'intv_tx'    : '333',
        'shutdown'   : '',
        'source_intf': dum_if,
        },
    '2001:db8::a' : {
        'source_addr': '2001:db8::1',
        'source_intf': dum_if,
        },
    '2001:db8::b' : {
        'source_addr': '2001:db8::1',
        'multihop'   : '',
        },
}

profiles = {
    'foo' : {
        'echo_mode'  : '',
        'intv_echo'  : '100',
        'intv_mult'  : '101',
        'intv_rx'    : '222',
        'intv_tx'    : '333',
        'shutdown'   : '',
        },
    'bar' : {
        'intv_mult'  : '102',
        'intv_rx'    : '444',
        },
}

class TestProtocolsBFD(VyOSUnitTestSHIM.TestCase):
    def tearDown(self):
        self.cli_delete(base_path)
        self.cli_commit()
        # Check for running process
        self.assertTrue(process_named_running(PROCESS_NAME))

    def test_bfd_peer(self):
        for peer, peer_config in peers.items():
            if 'echo_mode' in peer_config:
                self.cli_set(base_path + ['peer', peer, 'echo-mode'])
            if 'intv_echo' in peer_config:
                self.cli_set(base_path + ['peer', peer, 'interval', 'echo-interval', peer_config["intv_echo"]])
            if 'intv_mult' in peer_config:
                self.cli_set(base_path + ['peer', peer, 'interval', 'multiplier', peer_config["intv_mult"]])
            if 'intv_rx' in peer_config:
                self.cli_set(base_path + ['peer', peer, 'interval', 'receive', peer_config["intv_rx"]])
            if 'intv_tx' in peer_config:
                self.cli_set(base_path + ['peer', peer, 'interval', 'transmit', peer_config["intv_tx"]])
            if 'multihop' in peer_config:
                self.cli_set(base_path + ['peer', peer, 'multihop'])
            if 'shutdown' in peer_config:
                self.cli_set(base_path + ['peer', peer, 'shutdown'])
            if 'source_addr' in peer_config:
                self.cli_set(base_path + ['peer', peer, 'source', 'address', peer_config["source_addr"]])
            if 'source_intf' in peer_config:
                self.cli_set(base_path + ['peer', peer, 'source', 'interface', peer_config["source_intf"]])

        # commit changes
        self.cli_commit()

        # Verify FRR bgpd configuration
        frrconfig = self.getFRRconfig('bfd')
        for peer, peer_config in peers.items():
            tmp = f'peer {peer}'
            if 'multihop' in peer_config:
                tmp += f' multihop'
            if 'source_addr' in peer_config:
                tmp += f' local-address {peer_config["source_addr"]}'
            if 'source_intf' in peer_config:
                tmp += f' interface {peer_config["source_intf"]}'

            self.assertIn(tmp, frrconfig)
            peerconfig = self.getFRRconfig(f' peer {peer}', end='')

            if 'echo_mode' in peer_config:
                self.assertIn(f'echo-mode', peerconfig)
            if 'intv_echo' in peer_config:
                self.assertIn(f'echo-interval {peer_config["intv_echo"]}', peerconfig)
            if 'intv_mult' in peer_config:
                self.assertIn(f'detect-multiplier {peer_config["intv_mult"]}', peerconfig)
            if 'intv_rx' in peer_config:
                self.assertIn(f'receive-interval {peer_config["intv_rx"]}', peerconfig)
            if 'intv_tx' in peer_config:
                self.assertIn(f'transmit-interval {peer_config["intv_tx"]}', peerconfig)
            if 'shutdown' in peer_config:
                self.assertIn(f'shutdown', peerconfig)
            else:
                self.assertNotIn(f'shutdown', peerconfig)

    def test_bfd_profile(self):
        peer = '192.0.2.10'

        for profile, profile_config in profiles.items():
            if 'echo_mode' in profile_config:
                self.cli_set(base_path + ['profile', profile, 'echo-mode'])
            if 'intv_echo' in profile_config:
                self.cli_set(base_path + ['profile', profile, 'interval', 'echo-interval', profile_config["intv_echo"]])
            if 'intv_mult' in profile_config:
                self.cli_set(base_path + ['profile', profile, 'interval', 'multiplier', profile_config["intv_mult"]])
            if 'intv_rx' in profile_config:
                self.cli_set(base_path + ['profile', profile, 'interval', 'receive', profile_config["intv_rx"]])
            if 'intv_tx' in profile_config:
                self.cli_set(base_path + ['profile', profile, 'interval', 'transmit', profile_config["intv_tx"]])
            if 'shutdown' in profile_config:
                self.cli_set(base_path + ['profile', profile, 'shutdown'])

        self.cli_set(base_path + ['peer', peer, 'profile', list(profiles)[0]])

        # commit changes
        self.cli_commit()

        # Verify FRR bgpd configuration
        for profile, profile_config in profiles.items():
            config = self.getFRRconfig(f' profile {profile}', endsection='^ !')
            if 'echo_mode' in profile_config:
                self.assertIn(f'echo-mode', config)
            if 'intv_echo' in profile_config:
                self.assertIn(f'echo-interval {profile_config["intv_echo"]}', config)
            if 'intv_mult' in profile_config:
                self.assertIn(f'detect-multiplier {profile_config["intv_mult"]}', config)
            if 'intv_rx' in profile_config:
                self.assertIn(f'receive-interval {profile_config["intv_rx"]}', config)
            if 'intv_tx' in profile_config:
                self.assertIn(f'transmit-interval {profile_config["intv_tx"]}', config)
            if 'shutdown' in profile_config:
                self.assertIn(f'shutdown', config)
            else:
                self.assertNotIn(f'shutdown', config)

if __name__ == '__main__':
    unittest.main(verbosity=2)
