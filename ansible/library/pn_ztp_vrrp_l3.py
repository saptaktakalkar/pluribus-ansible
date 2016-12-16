#!/usr/bin/python
""" PN CLI Zero Touch Provisioning (ZTP) with VRRP """

#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

import shlex
import time

DOCUMENTATION = """
---
module: pn_ztp
author: "Pluribus Networks (@gauravbajaj)"
version: 1
short_description: CLI command to do zero touch provisioning with vrrp.
description:
    Zero Touch Provisioning (ZTP) allows you to provision new switches in your
    network automatically, without manual intervention.
    It performs following steps:
        - Configure VRRP for the gateway(extension of l2
          in the ZTP module)

options: TO DO
"""


def pn_cli(module):
    """
    This method is to generate the cli portion to launch the Netvisor cli.
    It parses the username, password, switch parameters from module.
    :param module: The Ansible module to fetch username, password and switch
    :return: The cli string for further processing
    """
    username = module.params['pn_cliusername']
    password = module.params['pn_clipassword']
    cliswitch = module.params['pn_cliswitch']

    if username and password:
        cli = '/usr/bin/cli --quiet --user %s:%s' % (username, password)
    else:
        cli = '/usr/bin/cli --quiet '

    if cliswitch:
        cli += ' switch ' + cliswitch

    return cli


def run_cli(module, cli):
    """
    This method executes the cli command on the target node(s) and returns the
    output.
    :param module: The Ansible module to fetch input parameters.
    :param cli: the complete cli string to be executed on the target node(s).
    :return: Output/Error or Success message depending upon.
    the response from cli.
    """
    cli = shlex.split(cli)
    rc, out, err = module.run_command(cli)
    if out:
        return out

    if err:
        module.exit_json(
            error="1",
            failed=True,
            stderr=err.strip(),
            msg="Operation Failed: " + str(cli),
            changed=False
            )
    else:
        return 'Success'


def create_vlan(module, start, end):
    """
    This method is to create vlans.
    :param module: The Ansible module to fetch input parameters.
    :param start: Start of the vlan range for vlans to be created.
    :param end: End of the vlan range for vlans to be created.
    :return: Success or failure message for the vlans.
    """
    vlan = []
    output = ' '
    cli = pn_cli(module)
    clicopy = cli
    clicopy += ' vlan-show format id no-show-headers '
    already_vlan_id = run_cli(module, clicopy).split()
    already_vlan_id = list(set(already_vlan_id))

    vlan_id = int(start)
    while vlan_id < int(end):
        id_str = str(vlan_id)
        vlan.append(id_str)
        if id_str not in already_vlan_id:
            clicopy = cli
            clicopy += ' vlan-create id '
            clicopy += id_str
            clicopy += ' scope fabric '
            output += run_cli(module, clicopy)
            output += ' '

        vlan_id += 1

    return vlan


def create_l3_vrouter(module, switch, vrrp_id):
    """
    This method is to create vrouter and assign vrrp_id to the switches.
    :param module: The Ansible module to fetch input parameters.
    :param switch: The switch name on which vrouter will be created.
    :param vrrp_id: The vrrp_id to be assigned.
    :return: The output string informing details of vrouter created and
    interface added or if vrouter already exists.
    """
    output = ' '
    switch_temp = switch[3:]
    vrouter_name = switch_temp
    vnet_name = module.params['pn_fabric_name'] + '-global'
    cli = pn_cli(module)
    if 'switch' in cli:
        cli = cli.rpartition('switch')[0]

    cli += ' switch ' + switch
    cli_copy = cli

    # Check if vrouter already exists
    cli += ' vrouter-show format name no-show-headers '
    existing_vrouter_names = run_cli(module, cli).split()

    # If vrouter doesn't exists then create it
    if vrouter_name not in existing_vrouter_names:
        cli = cli_copy
        cli += ' vrouter-create name %s vnet %s hw-vrrp-id %s enable ' % (
            vrouter_name, vnet_name, vrrp_id)
        run_cli(module, cli)
        output += ' Created vrouter %s on switch %s ' % (vrouter_name, switch)
        output += '\n'
    else:
        output += ' Vrouter name %s on switch %s already exists. ' % (
            vrouter_name, switch)

    return output


def create_l3_interface(module, switch, ip, vlan_id, vrrp_id,
                        ip_count, vrrp_priority):
    """
    This method is to add vrouter interface and assign IP to it along with
    vrrp_id and vrrp_priority.
    :param module: The Ansible module to fetch input parameters.
    :param switch: The switch name on which vrouter will be created.
    :param ip: IP address to be assigned to vrouter interface.
    :param vlan_id: vlan_id to be assigned.
    :param vrrp_id: vrrp_id to be assigned.
    :param vrrp_priority: priority to be given(110 for active switch).
    :param ip_count: The value of fourth octet in the ip
    :return: The output string informing details of vrouter created and
    interface added or if vrouter already exists.
    """
    output = ' '
    cli = pn_cli(module)
    if 'switch' in cli:
        cli = cli.rpartition('switch')[0]

    clicopy = cli
    cli += ' vrouter-show location %s format name no-show-headers ' % switch
    vrouter_name = run_cli(module, cli).split()
    ip_addr = ip.split('.')
    fourth = ip_addr[3].split('/')
    subnet = fourth[1]

    first = ip_addr[0] + '.' + ip_addr[1] + '.' + ip_addr[2] + '.'
    ip1 = first + '1' + '/' + subnet
    ip2 = first + ip_count + '/' + subnet

    cli = clicopy
    cli += ' vrouter-interface-show vlan %s ip %s ' % (vlan_id, ip2)
    cli += ' format switch no-show-headers '
    existing_vrouter = run_cli(module, cli).split()
    existing_vrouter = list(set(existing_vrouter))

    if vrouter_name[0] not in existing_vrouter:
        cli = clicopy
        cli += ' vrouter-interface-add vrouter-name ' + vrouter_name[0]
        cli += ' ip ' + ip2
        cli += ' vlan %s if data ' % vlan_id
        run_cli(module, cli)
        output += ' and added vrouter interface with ip: ' + ip2
        output += ' '
    else:
        output += ' interface already exists for vrouter ' + vrouter_name[0]

    cli = clicopy
    cli += ' vrouter-interface-show vrouter-name %s ip %s vlan %s ' % (
        vrouter_name[0], ip2, vlan_id)
    cli += ' format nic no-show-headers '
    eth_port = run_cli(module, cli).split()
    eth_port.remove(vrouter_name[0])

    cli = clicopy
    cli += ' vrouter-interface-show vlan %s ip %s vrrp-primary %s ' % (
        vlan_id, ip1, eth_port[0])
    cli += ' format switch no-show-headers '
    existing_vrouter = run_cli(module, cli).split()
    existing_vrouter = list(set(existing_vrouter))

    if vrouter_name[0] not in existing_vrouter:
        cli = clicopy
        cli += ' vrouter-interface-add vrouter-name ' + vrouter_name[0]
        cli += ' ip ' + ip1
        cli += ' vlan %s if data vrrp-id %s ' % (vlan_id, vrrp_id)
        cli += ' vrrp-primary %s vrrp-priority %s ' % (eth_port[0],
                                                       vrrp_priority)
        output += run_cli(module, cli)
        output += ' '
    else:
        output += ' interface already added for vrouter ' + vrouter_name[0]

    return output


def leaf_no_cluster(module, leaf_list):
    """
    This method is to find leafs not in any leafs.
    :param module: The Ansible module to fetch input parameters.
    :param leaf_list: The list of all the leaf switches.
    :return: The list of leaf in no cluster.
    """
    cli = pn_cli(module)
    non_cluster_leaf = []
    if 'switch' in cli:
        cli = cli.rpartition('switch')[0]

    clicopy = cli
    clicopy += ' cluster-show format cluster-node-1 no-show-headers '
    cluster1 = run_cli(module, clicopy).split()
    clicopy = cli
    clicopy += ' cluster-show format cluster-node-2 no-show-headers '
    cluster2 = run_cli(module, clicopy).split()

    for leaf in leaf_list:
        if (leaf not in cluster1) and (leaf not in cluster2):
            non_cluster_leaf.append(leaf)

    return non_cluster_leaf


def create_cluster(module, switch, name, node1, node2):
    """
    This method is to create a cluster between two switches.
    :param module: The Ansible module to fetch input parameters.
    :param switch: Name of the local switch.
    :param name: The name of the cluster to create.
    :param node1: First node of the cluster.
    :param node2: Second node of the cluster.
    :return: The output of run_cli() method.
    """
    cli = pn_cli(module)
    if 'switch' in cli:
        cli = cli.rpartition('switch')[0]

    clicopy = cli
    cli += ' switch %s cluster-show format name no-show-headers ' % node1
    cluster_list = run_cli(module, cli).split()
    if name not in cluster_list:
        cli = clicopy
        cli += ' switch %s cluster-create name %s ' % (switch, name)
        cli += ' cluster-node-1 %s cluster-node-2 %s ' % (node1, node2)
        return run_cli(module, cli)
    else:
        return "Already part of a cluster"


def leaf_cluster_formation(module, non_cluster_leaf, spine_list):
    """
    This method uses non-clustered leafs and forms cluster.
    :param module: The Ansible module to fetch input parameters.
    :param non_cluster_leaf: List of all the leaf not in cluster.
    :param spine_list: The list of spines.
    :return: The output message of success or error
    """
    cli = pn_cli(module)
    if 'switch' in cli:
        cli = cli.rpartition('switch')[0]

    clicopy = cli
    output = ' '
    flag = 0
    while flag == 0:
        if len(non_cluster_leaf) == 0:
            output += "no more leaf to create cluster"
            output += ' '
            flag += 1
        else:
            node1 = non_cluster_leaf[0]
            non_cluster_leaf.remove(node1)
            cli = clicopy
            cli += ' switch %s lldp-show format sys-name ' % node1
            cli += ' no-show-headers '
            system_names = run_cli(module, cli).split()
            system_names = list(set(system_names))

            flag1 = 0
            switch_count = 0
            while (switch_count < len(system_names)) and (flag1 == 0):
                switch = system_names[switch_count]
                if switch not in spine_list:
                    if switch in non_cluster_leaf:
                        name = node1 + '-to-' + switch + '-cluster'
                        output += create_cluster(module, switch, name, node1,
                                                 switch)
                        output += ' '
                        non_cluster_leaf.remove(switch)
                        flag1 += 1
                    else:
                        output += "switch already has a cluster"
                else:
                    output += "switch is a spine"

                switch_count += 1

    return output


def create_leaf_cluster(module):
    """
    This method creates leaf cluster with physical link.
    :param module: The Ansible module to fetch input parameters.
    :return: The output message with success or error.
    """
    output = ' '
    spine_list = module.params['pn_spine_list']
    leaf_list = module.params['pn_leaf_list']
    non_cluster_leaf = leaf_no_cluster(module, leaf_list)
    output += leaf_cluster_formation(module, non_cluster_leaf, spine_list)
    output += ' '
    return output


def configure_vrrp(module, vrrp_id, no_interface, vrrp_ip,
                   active_switch, vlan_range):
    """
    This method is to configure vrrp.
    :param module: The Ansible module to fetch input parameters.
    :param vrrp_id: The vrrp_id need to be assigned.
    :param no_interface: The number of interfaces to be added.
    :param vrrp_ip: The vrrp_ip needed to be assigned.
    :param active_switch: The name of the active switch.
    :param vlan_range: The vlan_range for creating the vlans.
    :return: It returns the output of the configuration
    """
    output = ' '
    cli = pn_cli(module)
    if 'switch' in cli:
        cli = cli.rpartition('switch')[0]

    clicopy = cli
    output += create_leaf_cluster(module)
    vlan_range_split = vlan_range.split('-')
    start = vlan_range_split[0]
    end_no_interface = int(start) + int(no_interface)
    vlan = create_vlan(module, start, end_no_interface)

    output += ' vlans created '
    vrrp_ip_segment = vrrp_ip.split('.')
    host_count = 1

    cli = clicopy
    cli += ' cluster-show format name no-show-headers '
    cluster_name = run_cli(module, cli).split()
    for cluster in cluster_name:
        switch_list = []
        cli = clicopy
        cli += ' cluster-show name %s format cluster-node-1 ' % cluster
        cli += ' no-show-headers '
        switch1 = run_cli(module, cli)
        cli = clicopy
        cli += ' cluster-show name %s format cluster-node-2 ' % cluster
        cli += ' no-show-headers '
        switch2 = run_cli(module, cli)
        switch_list.append(switch1)
        switch_list.append(switch2)

        for switch in switch_list:
            output += create_l3_vrouter(module, switch, vrrp_id)
            output += ' '

        for switch in switch_list:
            host_count += 1
            if switch == active_switch:
                vrrp_priority = '110'
            else:
                vrrp_priority = '100'

            for vlan_id in vlan:
                ip = vrrp_ip_segment[0] + '.' + vrrp_ip_segment[1] + '.'
                ip += vlan_id + '.' + vrrp_ip_segment[3]
                output += create_l3_interface(module, switch, ip, vlan_id,
                                              vrrp_id, str(host_count),
                                              vrrp_priority)
                if int(vlan_id) % 15 == 0:
                    output += ' waiting for 2 sec '
                    time.sleep(2)

    return output


def main():
    """ This section is for arguments parsing """
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=False, type='str'),
            pn_clipassword=dict(required=False, type='str', no_log=True),
            pn_cliswitch=dict(required=False, type='str'),
            pn_fabric_name=dict(required=False, type='str'),
            pn_fabric_network=dict(required=False, type='str',
                                   choices=['mgmt', 'in-band'],
                                   default='mgmt'),
            pn_fabric_type=dict(required=False, type='str',
                                choices=['layer2', 'layer3'],
                                default='layer2'),
            pn_fabric_retry=dict(required=False, type='int', default=1),
            pn_run_l2_l3=dict(required=False, type='bool', default=False),
            pn_net_address=dict(required=False, type='str'),
            pn_cidr=dict(required=False, type='str'),
            pn_supernet=dict(required=False, type='str'),
            pn_spine_list=dict(required=False, type='list'),
            pn_leaf_list=dict(required=False, type='list'),
            pn_update_fabricto_inband=dict(required=False, type='bool',
                                           default=False),
            pn_assign_loopback=dict(required=False, type='bool', default=False),
            pn_loopback_ip=dict(required=False, type='str',
                                default='101.101.101.0/32'),
            pn_inband_ip=dict(required=False, type='str',
                              default='172.16.0.0/24'),
            pn_fabric_control_network=dict(required=False, type='str',
                                           choices=['mgmt', 'in-band'],
                                           default='mgmt'),
            pn_protocol=dict(required=False, type='str'),
            pn_vrrp_id=dict(required=False, type='str', default='18'),
            pn_vrrp_ip=dict(required=False, type='str',
                            dafault='101.101.$.0/24'),
            pn_active_switch=dict(required=False, type='str',
                                  default='auto-spine1'),
            pn_vlan_range=dict(required=False, type='str', default='101-200'),
            pn_vrrp_no_interface=dict(required=False, type='str', default='4'),
        )
    )

    message = ' '
    vrrp_id = module.params['pn_vrrp_id']
    no_interface = module.params['pn_vrrp_no_interface']
    vrrp_ip = module.params['pn_vrrp_ip']
    active_switch = module.params['pn_active_switch']
    vlan_range = module.params['pn_vlan_range']
    message += ' '
    message += configure_vrrp(module, vrrp_id, no_interface, vrrp_ip,
                              active_switch, vlan_range)
    message += ' '

    module.exit_json(
        stdout=message,
        error="0",
        failed=False,
        msg="Operation Completed",
        changed=True
        )

# AnsibleModule boilerplate
from ansible.module_utils.basic import AnsibleModule

if __name__ == '__main__':
    main()

