#!/usr/bin/env python3

import json
import os
import sys
import time
from netaddr import IPNetwork

from vyos.configquery import ConfigTreeQuery
from vyos.util import commit_in_progress
from vyos.util import dict_search_args

sub_delegation_data = '/run/dhcp-server/sd.json'
config_file_sub_delegation = '/run/dhcp-server/dhcpdv6_sd.conf'

ifname = os.environ['IFNAME']
reason = os.environ['REASON']
pd_info = os.environ['PDINFO']

def get_config():
    base = ['service', 'dhcpv6-server']
    conf = ConfigTreeQuery()

    if not conf.exists(base):
        return None

    return conf.get_config_dict(base,
        key_mangling=('-', '_'), get_first_key=True,
        no_tag_node_value_mangle=True)

if __name__ == '__main__':
    # Wait for any commit finish
    while commit_in_progress():
        time.sleep(1)

    dhcp_conf = get_config()

    if 'shared_network_name' not in dhcp_conf:
        sys.exit(0)

    ifdata = {}

    if os.path.exists(sub_delegation_data):
        with open(sub_delegation_data, 'r') as f:
            ifdata = json.loads(f.read())

    if reason == 'REQUEST':
        if_net = IPNetwork(pd_info)
        if_quad = list(net.network.words)

        for shared_name, shared_conf in dhcp_conf['shared_network_name'].items():
            if_conf = dict_search_args(shared_conf, 'sub_delegation', ifname)

            if not if_conf:
                continue

            start_quad = if_quad.copy()
            start_quad[3] = start_quad[3] + int(if_conf['delegation_offset'])
            start_prefix = ':'.join([str(hex(i)).lstrip('0x') for i in start_quad][0:4]) + '::'

            end_quad = start_quad.copy()
            end_quad[3] = end_quad[3] + int(if_conf['delegation_range']) - 1
            end_prefix = ':'.join([str(hex(i)).lstrip('0x') for i in end_quad][0:4]) + '::'

            ifdata[ifname] = {
                'prefix_start': start_prefix,
                'prefix_end': end_prefix
            }

        dhcp_conf['ifdata'] = ifdata

        render(config_file_sub_delegation, 'dhcp-server/dhcpv6_sd.conf.j2', dhcp_conf)

    with open(sub_delegation_data, 'w') as f:
        f.write(json.dumps(ifdata))
