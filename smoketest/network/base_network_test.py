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

import json
import os
import socket
import sys
import unittest

from time import sleep
from typing import Type

from vyos.configsession import ConfigSession
from vyos.configsession import ConfigSessionError
from vyos import ConfigError
from vyos.defaults import commit_lock
from vyos.util import cmd
from vyos.util import run

test_interface = 'eth0'
test_address = '192.0.2.{}'
test_suffix = '/24'
test_port = 5555

save_config = '/tmp/vyos-smoketest-save'

# This class acts as shim between individual Smoketests developed for VyOS and
# the Python UnitTest framework. Before every test is loaded, we dump the current
# system configuration and reload it after the test - despite the test results.
#
# Using this approach we can not render a live system useless while running any
# kind of smoketest. In addition it adds debug capabilities like printing the
# command used to execute the test.
class VyOSNetworkUnitTest:
    class TestCase(unittest.TestCase):
        # if enabled in derived class, print out each and every set/del command
        # on the CLI. This is usefull to grap all the commands required to
        # trigger the certain failure condition.
        # Use "self.debug = True" in derived classes setUp() method
        debug = True
        required_agents = 1

        @classmethod
        def setUpClass(cls):
            cls.available_agents = int(os.environ['VYOS_AGENTS'])

            if cls.available_agents < cls.required_agents:
                cls.skipTest(cls, reason='not enough agents available')

            cls._session = ConfigSession(os.getpid())
            cls._session.save_config(save_config)
            
            cls.cli_set(cls, ['firewall', 'all-ping', 'enable'])
            cls.cli_set(cls, ['interfaces', 'ethernet', test_interface, 'address', '192.0.2.1/24'])
            cls.cli_commit(cls)

        @classmethod
        def tearDownClass(cls):
            # shutdown agents on final test teardown
            if 'VYOS_AGENT_SHUTDOWN' in os.environ:
                for i in range(1, cls.available_agents + 1):
                    cls.agent_command(cls, i, 'shutdown')

            # discard any pending changes which might caused a messed up config
            cls._session.discard()
            # ... and restore the initial state
            cls._session.migrate_and_load_config(save_config)

            try:
                cls._session.commit()
            except (ConfigError, ConfigSessionError):
                cls._session.discard()
                cls.fail(cls)

        def tearDown(self):
            for agent in range(1, self.required_agents + 1):
                self.agent_command(agent, 'tear_down')

        def agent_command(self, agent, action, data={}):
            ip_addr = test_address.format(agent + 1) # agents start at x.x.x.2

            retval = None
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(10)
                try:
                    sock.connect((ip_addr, test_port))

                    msg = json.dumps({'action': action, 'data': data})
                    sock.sendall(bytes(msg, 'ascii'))

                    data = sock.recv(8192)

                    if data:
                        retval = json.loads(data)
                except:
                    retval = None

            return retval

        def agents_wait(self, max_count=30):
            success = []
            count = 0
            while len(success) < self.required_agents:
                self.assertTrue(count < max_count, msg='Max count reached while waiting for agents')

                for agent in range(1, self.required_agents + 1):
                    if agent in success:
                        continue

                    ip_addr = test_address.format(agent + 1) # agents start at x.x.x.2
                    code = run(f'ping -c 1 -w 1 {ip_addr}')
                    if code == 0:
                        success.append(agent)

                count += 1
                sleep(1)

        def cli_set(self, config, agent=None):
            if self.debug:
                prefix = f'agent {agent}: ' if agent else ''
                print(prefix + 'set ' + ' '.join(config))
            if agent:
                ret_obj = self.agent_command(agent, 'set', {'config':config})

                if ret_obj and 'error' in ret_obj:
                    exception = ret_obj['error']
                    msg = ret_obj['message']
                    raise Exception(f'Agent {agent} Exception: {exception} - {msg}')
            else:
                self._session.set(config)

        def cli_delete(self, config, agent=None):
            if self.debug:
                prefix = f'agent {agent}: ' if agent else ''
                print(prefix + 'del ' + ' '.join(config))
            if agent:
                ret_obj = self.agent_command(agent, 'delete', {'config':config})

                if ret_obj and 'error' in ret_obj:
                    exception = ret_obj['error']
                    msg = ret_obj['message']
                    raise Exception(f'Agent {agent} Exception: {exception} - {msg}')
            else:
                self._session.delete(config)

        def cli_commit(self, agent=None):
            if agent:
                ret_obj = self.agent_command(agent, 'commit')

                if ret_obj and 'error' in ret_obj:
                    exception = ret_obj['error']
                    msg = ret_obj['message']
                    raise Exception(f'Agent {agent} Exception: {exception} - {msg}')
            else:
                self._session.commit()
                # during a commit there is a process opening commit_lock, and run() returns 0
                while run(f'sudo lsof -nP {commit_lock}') == 0:
                    sleep(0.250)

        def getFRRconfig(self, string, end='$', endsection='^!', daemon='', agent=None):
            """ Retrieve current "running configuration" from FRR """
            if agent:
                ret_obj = self.agent_command(agent, 'set', {'config':config})

                if ret_obj and 'error' in ret_obj:
                    exception = ret_obj['error']
                    msg = ret_obj['message']
                    raise Exception(f'Agent {agent} Exception: {exception} - {msg}')

                if 'data' not in ret_obj:
                    out = ''
                else:
                    out = ret_obj['data']
            else:
                command = f'vtysh -c "show run {daemon} no-header" | sed -n "/^{string}{end}/,/{endsection}/p"'
                out = cmd(command)
            if self.debug:
                import pprint
                prefix = f'agent {agent}: ' if agent else ''
                print(f'\n\n{prefix} command "{command}" returned:\n')
                pprint.pprint(out)
            return out

# standard construction; typing suggestion: https://stackoverflow.com/a/70292317
def ignore_warning(warning: Type[Warning]):
    import warnings
    from functools import wraps

    def inner(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=warning)
                return f(*args, **kwargs)
        return wrapped
    return inner
