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

import unittest

from base_network_test import VyOSNetworkUnitTest

from vyos.util import run

class TestBasic(VyOSNetworkUnitTest.TestCase):
    required_agents = 1

    @classmethod
    def setUpClass(cls):
        super(TestBasic, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        super(TestBasic, cls).tearDownClass()

    def tearDown(self):
        super().tearDown()

    def test_ping(self):
        self.agents_wait()

        # Set local address
        self.cli_set(['interfaces', 'ethernet', 'eth1', 'address', '198.51.100.1/24'])
        self.cli_commit()

        # Set agent address
        self.cli_set(['interfaces', 'ethernet', 'eth1', 'address', '198.51.100.2/24'], agent=1)
        self.cli_commit(agent=1)

        code = run('ping -c 1 192.0.2.2') # Agent 1 via agent interface
        self.assertTrue(code == 0)

        code = run('ping -c 1 198.51.100.2') # Agent 1 via test interface
        self.assertTrue(code == 0)

if __name__ == '__main__':
    unittest.main(verbosity=2)
