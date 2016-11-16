#!/usr/bin/python
""" PN CLI Zero Touch Provisioning (ZTP) """

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

DOCUMENTATION = """
---
module: pn_ztp
author: "Pluribus Networks (@saptaktakalkar)"
version: 1
short_description: CLI command to do zero touch provisioning.
description:
    Zero Touch Provisioning (ZTP) allows you to provision new switches in your
    network automatically, without manual intervention.
    It performs following steps:
        - Accept EULA
        - Disable STP
        - Enable all ports
        - Create/Join fabric
        - For Layer 2 fabric: Auto configure vlags
        - For layer 3 fabric: Auto configure link IPs
        - Change fabric type to in-band
        - Enable STP
options:
    pn_cliusername:
        description:
          - Provide login username if user is not root.
        required: False
        type: str
    pn_clipassword:
      description:
        - Provide login password if user is not root.
      required: False
      type: str
    pn_cliswitch:
      description:
        - Target switch(es) to run the CLI on.
      required: False
      type: str
    pn_fabric_name:
      description:
        - Specify name of the fabric.
      required: False
      type: str
    pn_fabric_network:
      description:
        - Specify fabric network type as either mgmt or in-band.
      required: False
      type: str
      choices: ['mgmt', 'in-band']
      default: 'mgmt'
    pn_fabric_type:
      description:
        - Specify fabric type as either layer2 or layer3.
      required: False
      type: str
      choices: ['layer2', 'layer3']
      default: 'layer2'
    pn_run_l2_l3:
      description:
        - Boolean flag to decide whether to configure vlag and link IPs or not.
      required: False
      type: bool
      default: False
    pn_net_address:
      description:
        - Specify network address to be used in configuring link IPs for layer3.
      required: False
      type: str
    pn_cidr:
      description:
        - Specify CIDR value to be used in configuring link IPs for layer3.
      required: False
      type: str
    pn_supernet:
      description:
        - Specify supernet value to be used in configuring link IPs for layer3.
      required: False
      type: str
"""

EXAMPLES = """
- name: Zero Touch Provisioning - Initial setup
  pn_ztp:
    pn_cliusername: "{{ USERNAME }}"
    pn_clipassword: "{{ PASSWORD }}"
    pn_fabric_name: ztp-fabric
    pn_run_l2_l3: False

- name: Zero Touch Provisioning - Layer2/Layer3 setup
  pn_ztp:
    pn_cliusername: "{{ USERNAME }}"
    pn_clipassword: "{{ PASSWORD }}"
    pn_cliswitch: squirtle
    pn_fabric_type: layer3
    pn_run_l2_l3: True
    pn_net_address: '192.168.0.1'
    pn_cidr: '24'
    pn_supernet: '30'
"""

RETURN = """
msg:
  description: The set of responses for each command.
  returned: always
  type: str
changed:
  description: Indicates whether the CLI caused changes on the target.
  returned: always
  type: bool
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
        cli = '/usr/bin/cli --quiet --user %s:%s ' % (username, password)
    else:
        cli = '/usr/bin/cli --quiet '

    if cliswitch == 'local':
        cli += ' switch-local '
    else:
        cli += ' switch ' + cliswitch
    return cli


def run_cli(module, cli):
    """
    This method executes the cli command on the target node(s) and returns the
    output.
    :param module: The Ansible module to fetch input parameters.
    :param cli: the complete cli string to be executed on the target node(s).
    :return: Output/Error or Success message depending upon the response from cli.
    """
    cli = shlex.split(cli)
    rc, out, err = module.run_command(cli)

    if out:
        return out

    if err:
        module.exit_json(
            stderr=err.strip(),
            msg="Operation Failed: " + cli,
            changed=False
        )
    else:
        return 'Success'


def auto_accept_eula(module):
    """
    This method is to accept the EULA when we first login to new switch.
    :param module: The Ansible module to fetch input parameters.
    :return: The output of run_cli() method.
    """
    password = module.params['pn_clipassword']
    cli = '/usr/bin/cli --quiet '
    cli += ' --skip-setup --script-password switch-setup-modify '
    cli += ' eula-accepted true password ' + password
    return run_cli(module, cli)


def modify_stp(module, modify_flag):
    """
    This method is to enable/disable STP (Spanning Tree Protocol) of a switch.
    :param module: The Ansible module to fetch input parameters.
    :param modify_flag: Enable/disable flag to set.
    :return: The output of run_cli() method.
    """
    cli = pn_cli(module)
    cli += ' stp-modify ' + modify_flag
    return run_cli(module, cli)


def enable_ports(module):
    """
    This method is to enable all ports of a switch.
    :param module: The Ansible module to fetch input parameters.
    :return: The output of run_cli() method.
    """
    cli = pn_cli(module)
    cli += ' port-config-show format port no-show-headers '
    out = run_cli(module, cli)

    if out:
        ports = ','.join(out.split())
        cli = pn_cli(module)
        cli += ' port-config-modify port %s enable ' % ports
        return run_cli(module, cli)
    else:
        return out


def create_fabric(module, fabric_name, fabric_network):
    """
    This method is to create a fabric with default fabric type as mgmt.
    :param module: The Ansible module to fetch input parameters.
    :param fabric_name: Name of the fabric to create.
    :param fabric_network: Type of the fabric to create (mgmt/inband). Default value: mgmt
    :return: The output of run_cli() method.
    """
    cli = pn_cli(module)
    cli += ' fabric-create name ' + fabric_name
    cli += ' fabric-network ' + fabric_network
    return run_cli(module, cli)


def join_fabric(module, fabric_name):
    """
    This method is for a switch to join already existing fabric.
    :param module: The Ansible module to fetch input parameters.
    :param fabric_name: Name of the fabric to join.
    :return: The output of run_cli() method.
    """
    cli = pn_cli(module)
    cli += ' fabric-join name ' + fabric_name
    return run_cli(module, cli)


def update_fabric_network_to_inband(module):
    """
    This method is to update fabric network type to in-band
    :param module: The Ansible module to fetch input parameters.
    :return: The output of run_cli() method.
    """
    cli = pn_cli(module)
    cli += ' modify fabric-local fabric-network in-band '
    return run_cli(module, cli)


def calculate_link_ip_addresses(address_str, cidr_str, supernet_str):
    """
    This method is to calculate link IPs for layer 3 fabric
    :param address_str: Host/network address.
    :param cidr_str: Subnet mask.
    :param supernet_str: Supernet mask
    :return: List of available IP addresses that can be assigned to vrouter
    interfaces for layer 3 fabric.
    """
    # Split address into octets and turn CIDR, supernet mask into int
    address = address_str.split('.')
    cidr = int(cidr_str)
    supernet = int(supernet_str)
    supernet_mapping = {
        30: 2,
        29: 6,
        28: 14,
        27: 30
    }
    supernet_range = supernet_mapping[supernet]

    # Initialize the netmask and calculate based on CIDR mask
    mask = [0, 0, 0, 0]
    for i in range(cidr):
        mask[i / 8] += (1 << (7 - i % 8))

    # Initialize net and binary and netmask with addr to get network
    network = []
    for i in range(4):
        network.append(int(address[i]) & mask[i])

    # Duplicate net into broad array, gather host bits, and generate broadcast
    broadcast = list(network)
    broadcast_range = 32 - cidr
    for i in range(broadcast_range):
        broadcast[3 - i / 8] += (1 << (i % 8))

    last_ip = list(broadcast)
    i, count, hostmin, hostmax = 0, 0, 0, 0
    ips_list = []

    while count < last_ip[3]:
        hostmin = i + 1
        hostmax = hostmin + supernet_range - 1
        while hostmin <= hostmax:
            ips_list.append(hostmin)
            hostmin += 1

        i = hostmax + 2
        count = i

    available_ips = []
    list_index = 0
    ip_address = str(last_ip[0]) + '.' + str(last_ip[1]) + '.' + str(last_ip[2])
    while list_index < len(ips_list):
        ip = ip_address + '.' + str(ips_list[list_index])
        available_ips.append(ip)
        list_index += 1

    return available_ips


def create_vrouter_and_interface(module, switch, available_ips):
    """
    This method is to create vrouter and vrouter interface and assign IP to it.
    :param module: The Ansible module to fetch input parameters.
    :param switch: The switch name on which vrouter will be created.
    :param available_ips: List of available IP addresses to be assigned to vrouter interfaces.
    :return: The output string informing details of vrouter created and
    interface added or if vrouter already exists.
    """
    vrouter_name = switch + '-vrouter'
    vnet_name = module.params['pn_fabric_name'] + '-global'
    cli = pn_cli(module).rpartition('switch')[0]
    cli += ' switch ' + switch
    cli_copy = cli

    # Check if vrouter already exists
    cli += ' vrouter-show format name no-show-headers '
    existing_vrouter_names = run_cli(module, cli).split()

    # If vrouter doesn't exists then create it
    if vrouter_name not in existing_vrouter_names:
        cli = cli_copy
        cli += ' vrouter-create name %s vnet %s ' % (vrouter_name, vnet_name)
        run_cli(module, cli)
        output = ' Created vrouter %s on switch %s ' % (vrouter_name, switch)

        # Create vrouter interface and assign first available ip to it
        ip = available_ips[0]
        cli = cli_copy
        cli += ' vrouter-interface-add vrouter-name ' + vrouter_name
        cli += ' ip ' + ip
        run_cli(module, cli)
        available_ips.remove(ip)
        output += ' and added vrouter interface with ip: ' + ip
    else:
        output = ' Vrouter name %s on switch %s already exists. ' % (vrouter_name, switch)

    return output


def auto_configure_link_ips(module):
    """
    This method is to auto configure link IPs for layer3 fabric.
    :param module: The Ansible module to fetch input parameters.
    :return: The output of create_vrouter_and_interface() method.
    """
    cli = pn_cli(module)
    cli += ' lldp-show format sys-name no-show-headers '
    switch_names = run_cli(module, cli).split()

    address = module.params['pn_net_address']
    cidr = module.params['pn_cidr']
    supernet = module.params['pn_supernet']
    available_ips = calculate_link_ip_addresses(address, cidr, supernet)
    output = ' '

    for switch in switch_names:
        output += create_vrouter_and_interface(module, switch, available_ips)

    for switch in switch_names:
        cli = pn_cli(module).rpartition('switch')[0]
        cli += ' switch %s lldp-show format sys-name no-show-headers ' % switch
        sys_names = run_cli(module, cli).split()

        for sys in sys_names:
            output += create_vrouter_and_interface(module, sys, available_ips)

    return output


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
    cli = pn_cli(module).rpartition('switch')[0]
    cli += ' switch %s cluster-create name %s ' % (switch, name)
    cli += ' cluster-node-1 %s cluster-node-2 %s ' % (node1, node2)
    return run_cli(module, cli)


def get_ports(module, switch, peer_switch):
    """
    This method is to figure out connected ports between two switches.
    :param module: The Ansible module to fetch input parameters.
    :param switch: Name of the local switch.
    :param peer_switch: Name of the connected peer switch.
    :return: List of connected ports.
    """
    cli = pn_cli(module).rpartition('switch')[0]
    cli += ' switch %s port-show hostname %s' % (switch, peer_switch)
    cli += ' format port no-show-headers '
    return run_cli(module, cli).split()


def create_trunk(module, switch, name, ports):
    """
    This method is to create a trunk on a switch.
    :param module: The Ansible module to fetch input parameters.
    :param switch: Name of the local switch.
    :param name: The name of the trunk to create.
    :param ports: List of connected ports.
    :return: The output of run_cli() method.
    """
    cli = pn_cli(module).rpartition('switch')[0]
    cli += ' switch %s trunk-create name %s ' % (switch, name)
    cli += ' ports %s ' % ports
    return run_cli(module, cli)


def create_vlag(module, switch, name, port, peer_switch, peer_port):
    """
    This method is to create virtual link aggregation groups.
    :param module: The Ansible module to fetch input parameters.
    :param switch: Name of the local switch.
    :param name: The name of the vlag to create.
    :param port: List of local switch ports.
    :param peer_switch: Name of the peer switch.
    :param peer_port: List of peer switch ports.
    :return: The output of run_cli() method.
    """
    cli = pn_cli(module).rpartition('switch')[0]
    cli += ' switch %s vlag-create name %s port %s ' % (switch, name, port)
    cli += ' peer-switch %s peer-port %s mode active-active' % (peer_switch, peer_port)
    return run_cli(module, cli)


def configure_auto_vlag(module):
    """
    This method is to create and configure vlag.
    :param module: The Ansible module to fetch input parameters.
    :return: The output of run_cli() method.
    """
    spine_list = module.params['pn_spine_list']
    leaf_list = module.params['pn_leaf_list']
    spine1 = spine_list[0]
    spine2 = spine_list[1]

    # TODO: Call create cluster, trunk, get ports and create vlag.


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
            pn_run_l2_l3=dict(required=False, type='bool', default=False),
            pn_net_address=dict(required=False, type='str'),
            pn_cidr=dict(required=False, type='str'),
            pn_supernet=dict(required=False, type='str'),
            pn_spine_list=dict(required=False, type='list'),
            pn_leaf_list=dict(required=False, type='list')
        )
    )

    fabric_name = module.params['pn_fabric_name']
    fabric_network = module.params['pn_fabric_network']
    fabric_type = module.params['pn_fabric_type']
    run_l2_l3 = module.params['pn_run_l2_l3']
    message = ''

    if not run_l2_l3:
        message += auto_accept_eula(module)
        message += ' '
        message += modify_stp(module, 'disable')
        message += ' '
        message += enable_ports(module)
        message += ' '
        message += create_fabric(module, fabric_name, fabric_network)
        message += ' '
    else:
        if fabric_type == 'layer2':
            message += configure_auto_vlag(module)
        elif fabric_type == 'layer3':
            message += auto_configure_link_ips(module)

        message += ' '
        message += update_fabric_network_to_inband(module)
        message += ' '
        message += modify_stp(module, 'enable')
        message += ' '

    module.exit_json(
        stdout=message,
        msg="Operation Completed",
        changed=True
    )

# AnsibleModule boilerplate
from ansible.module_utils.basic import AnsibleModule

if __name__ == '__main__':
    main()

