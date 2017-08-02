#!/usr/bin/python
""" PN CLI Layer3 Zero Touch Provisioning (ZTP) """

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
from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = """
---
module: pn_l3_ztp_json
author: 'Pluribus Networks (devops@pluribusnetworks.com)'
short_description: CLI command to configure L3 zero touch provisioning.
description:
    Zero Touch Provisioning (ZTP) allows you to provision new switches in your
    network automatically, without manual intervention. It configures link ips.
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
    pn_spine_list:
      description:
        - Specify list of Spine hosts.
      required: False
      type: list
    pn_leaf_list:
      description:
        - Specify list of leaf hosts.
      required: False
      type: list
    pn_update_fabric_to_inband:
      description:
        - Flag to indicate if fabric network should be updated to in-band.
      required: False
      default: False
      type: bool
    pn_assign_loopback:
      description:
        - Flag to indicate if loopback ips should be assigned to vrouters
        in layer3 fabric.
      required: False
      default: False
      type: bool
    pn_loopback_ip:
      description:
        - Loopback ip value for vrouters in layer3 fabric.
      required: False
      default: 109.109.109.0/24
      type: str
    pn_bfd:
      description:
        - Flag to indicate if BFD config should be added to vrouter interfaces
        in case of layer3 fabric.
      required: False
      default: False
      type: bool
    pn_bfd_min_rx:
      description:
        - Specify BFD-MIN-RX value required for adding BFD configuration
        to vrouter interfaces.
      required: False
      type: str
    pn_bfd_multiplier:
      description:
        - Specify BFD_MULTIPLIER value required for adding BFD configuration
        to vrouter interfaces.
      required: False
      type: str
    pn_stp:
      description:
        - Flag to enable STP at the end.
      required: False
      default: False
      type: bool
"""

EXAMPLES = """
- name: Zero Touch Provisioning - Layer3 setup
  pn_l3_ztp:
    pn_cliusername: "{{ USERNAME }}"
    pn_clipassword: "{{ PASSWORD }}"
    pn_net_address: '192.168.0.1'
    pn_cidr: '24'
    pn_supernet: '30'
"""

RETURN = """
summary:
  description: It contains output of each configuration along with switch name.
  returned: always
  type: str
changed:
  description: Indicates whether the CLI caused changes on the target.
  returned: always
  type: bool
unreachable:
  description: Indicates whether switch was unreachable to connect.
  returned: always
  type: bool
failed:
  description: Indicates whether or not the execution failed on the target.
  returned: always
  type: bool
exception:
  description: Describes error/exception occurred while executing CLI command.
  returned: always
  type: str
task:
  description: Name of the task getting executed on switch.
  returned: always
  type: str
msg:
  description: Indicates whether configuration made was successful or failed.
  returned: always
  type: str
"""

CHANGED_FLAG = []


def pn_cli(module):
    """
    Method to generate the cli portion to launch the Netvisor cli.
    :param module: The Ansible module to fetch username and password.
    :return: The cli string for further processing.
    """
    username = module.params['pn_cliusername']
    password = module.params['pn_clipassword']

    if username and password:
        cli = '/usr/bin/cli --quiet --user %s:%s ' % (username, password)
    else:
        cli = '/usr/bin/cli --quiet '

    return cli


def run_cli(module, cli):
    """
    Method to execute the cli command on the target node(s) and returns the
    output.
    :param module: The Ansible module to fetch input parameters.
    :param cli: The complete cli string to be executed on the target node(s).
    :return: Output/Error or Success msg depending upon the response from cli.
    """
    cli = shlex.split(cli)
    rc, out, err = module.run_command(cli)
    results = []
    if out:
        return out

    if err:
        json_msg = {
            'switch': '',
            'output': u'Operation Failed: {}'.format(' '.join(cli))
        }
        results.append(json_msg)
        module.exit_json(
            unreachable=False,
            failed=True,
            exception='',
            summary=results,
            task='CLI commands to configure L3 zero touch provisioning',
            msg='L3 ZTP configuration failed',
            changed=False
        )
    else:
        return 'Success'


def modify_stp(module, modify_flag):
    """
    Method to enable/disable STP (Spanning Tree Protocol) on all switches.
    :param module: The Ansible module to fetch input parameters.
    :param modify_flag: Enable/disable flag to set.
    :return: The output of run_cli() method.
    """
    output = ''
    cli = pn_cli(module)
    clicopy = cli

    for switch in (module.params['pn_spine_list'] +
                   module.params['pn_leaf_list']):
        cli = clicopy
        cli += ' switch %s stp-show format enable ' % switch
        current_state = run_cli(module, cli).split()[1]
        if current_state != 'yes':
            cli = clicopy
            cli += ' switch ' + switch
            cli += ' stp-modify ' + modify_flag
            if 'Success' in run_cli(module, cli):
                output += ' %s: STP enabled \n' % switch
                CHANGED_FLAG.append(True)
        else:
            output += ' %s: STP is already enabled \n' % switch

    return output


def update_fabric_network_to_inband(module):
    """
    Method to update fabric network type to in-band
    :param module: The Ansible module to fetch input parameters.
    :return: The output of run_cli() method.
    """
    output = ''
    cli = pn_cli(module)
    clicopy = cli

    for switch in (module.params['pn_spine_list'] +
                   module.params['pn_leaf_list']):
        cli = clicopy
        cli += ' fabric-info format fabric-network '
        fabric_network = run_cli(module, cli).split()[1]
        if fabric_network != 'in-band':
            cli = clicopy
            cli += ' switch ' + switch
            cli += ' fabric-local-modify fabric-network in-band '
            if 'Success' in run_cli(module, cli):
                output += ' %s: Updated fabric network to in-band \n' % switch
                CHANGED_FLAG.append(True)
        else:
            output += ' %s: Fabric network is already in in-band \n' % switch

    return output


def find_network(address, mask):
    # Initialize net and binary and netmask with addr to get network
    network = []
    for i in range(8):
        network.append(int(address[i], 16) & mask[i])

    return network


def find_broadcast(network, cidr):
    broadcast = list(network)
    broadcast_range = 128 - cidr
    for i in range(broadcast_range):
        broadcast[7 - i / 16] += (1 << (i % 16))

    return broadcast

def find_mask(cidr):
    mask = [0, 0, 0, 0, 0, 0, 0, 0]
    for i in range(cidr):
        mask[i / 16] += (1 << (15 - i % 16))

    return mask


def calculate_link_ip_addresses(address_str, cidr_str, supernet_str, ip_count):
    if '::' in address_str:
        add_str = ''
        count = (address_str.count(':'))
        if address_str[-1] == ':':
            count -= 2
            while count < 7:
                add_str += ':0'
                count += 1
        else:
            while count < 8:
                add_str += ':0'
                count += 1
            add_str += ':'

        address_str = address_str.replace('::', add_str)

    address = address_str.split(':')
    cidr = int(cidr_str)
    supernet = int(supernet_str)

    mask_cidr = find_mask(cidr)
    network = find_network(address, mask_cidr)
    broadcast = find_broadcast(network, cidr)

    mask_supernet = find_mask(supernet)
    network_supernet = find_network(address, mask_supernet)
    broadcast_supernet = find_broadcast(network_supernet, supernet)

    initial_ip = network_supernet[7]


    while initial_ip <= broadcast[7]:
        ips_list = []
        no_of_ip = 0
        while initial_ip <= broadcast_supernet[7] and no_of_ip < ip_count:
            ip = list(network)
            ip[7] = initial_ip
            for i in range(0,8):
                ip[i] = hex(ip[i])[2:]
            ip = ':'.join(ip)
            ip += '/' + str(supernet)
            ips_list.append(ip)
            initial_ip += 1
            no_of_ip += 1

        network_supernet = list(broadcast_supernet)
        network_supernet[7] += 1
        broadcast_supernet = find_broadcast(network_supernet, supernet)
        initial_ip = network_supernet[7]
        yield ips_list


def create_vrouter(module, switch, vnet_name):
    """
    Method to create vrouter on a switch.
    :param module: The Ansible module to fetch input parameters.
    :param switch: The switch name on which vrouter will be created.
    :param vnet_name: The name of the vnet for vrouter creation.
    :return: String describing if vrouter got created or if it already exists.
    """
    global CHANGED_FLAG
    vrouter_name = switch + '-vrouter'
    cli = pn_cli(module)
    cli += ' switch ' + switch
    clicopy = cli

    # Check if vrouter already exists.
    cli += ' vrouter-show format name no-show-headers '
    existing_vrouter_names = run_cli(module, cli).split()

    # If vrouter doesn't exists then create it.
    if vrouter_name not in existing_vrouter_names:
        cli = clicopy
        cli += ' vrouter-create name %s vnet %s ' % (vrouter_name, vnet_name)
        cli += ' router-type hardware'
        run_cli(module, cli)
        CHANGED_FLAG.append(True)
        return ' %s: Created vrouter with name %s \n' % (switch, vrouter_name)
    else:
        return ' %s: Vrouter with name %s already exists \n' % (switch,
                                                                vrouter_name)


def create_interface(module, switch, ip, port):
    """
    Method to create vrouter interface and assign IP to it.
    :param module: The Ansible module to fetch input parameters.
    :param switch: The switch name on which vrouter will be created.
    :param ip: IP address to be assigned to vrouter interfaces.
    :param port: l3-port for the interface.
    :return: The output string informing details of vrouter created and
    interface added or if vrouter already exists.
    """
    output = ''
    global CHANGED_FLAG
    cli = pn_cli(module)
    clicopy = cli
    cli += ' vrouter-show location %s format name no-show-headers ' % switch
    vrouter_name = run_cli(module, cli).split()[0]

    cli = clicopy
    cli += ' vrouter-interface-show l3-port %s ip %s ' % (port, ip)
    cli += ' format switch no-show-headers '
    existing_vrouter = run_cli(module, cli).split()
    existing_vrouter = list(set(existing_vrouter))

    if vrouter_name not in existing_vrouter:
        # Add vrouter interface.
        cli = clicopy
        cli += ' vrouter-interface-add vrouter-name ' + vrouter_name
        cli += ' ip ' + ip
        cli += ' l3-port ' + port
        run_cli(module, cli)
        output += ' %s: Added vrouter interface with ip %s on %s \n' % (
            switch, ip, vrouter_name
        )

        # Add BFD config to vrouter interface.
        if module.params['pn_bfd']:
            cli = clicopy
            cli += ' vrouter-interface-show vrouter-name ' + vrouter_name
            cli += ' l3-port %s format nic no-show-headers ' % port
            nic = run_cli(module, cli).split()[1]

            cli = clicopy
            cli += ' vrouter-interface-config-add '
            cli += ' vrouter-name %s nic %s ' % (vrouter_name, nic)
            cli += ' bfd-min-rx ' + module.params['pn_bfd_min_rx']
            cli += ' bfd-multiplier ' + module.params['pn_bfd_multiplier']
            run_cli(module, cli)
            output += ' %s: Added BFD config to %s \n' % (switch, vrouter_name)

        CHANGED_FLAG.append(True)
    else:
        output += ' %s: Vrouter interface %s already exists on %s \n' % (
            switch, ip, vrouter_name
        )

    return output


def modify_auto_trunk_setting(module, switch, flag):
    """
    Method to enable/disable auto trunk setting of a switch.
    :param module: The Ansible module to fetch input parameters.
    :param switch: Name of the local switch.
    :param flag: Enable/disable flag for the cli command.
    :return: The output of run_cli() method.
    """
    cli = pn_cli(module)
    if flag.lower() == 'enable':
        cli += ' switch %s system-settings-modify auto-trunk ' % switch
        return run_cli(module, cli)
    elif flag.lower() == 'disable':
        cli += ' switch %s system-settings-modify no-auto-trunk ' % switch
        return run_cli(module, cli)


def delete_trunk(module, switch, switch_port, peer_switch):
    """
    Method to delete a conflicting trunk on a switch.
    :param module: The Ansible module to fetch input parameters.
    :param switch: Name of the local switch.
    :param switch_port: The l3-port which is part of conflicting trunk for l3.
    :param peer_switch: Name of the peer switch.
    :return: String describing if trunk got deleted or not.
    """
    cli = pn_cli(module)
    clicopy = cli

    cli += ' switch %s port-show port %s hostname %s ' % (switch, switch_port,
                                                          peer_switch)
    cli += ' format trunk no-show-headers '
    trunk = run_cli(module, cli).split()
    trunk = list(set(trunk))
    if 'Success' not in trunk and len(trunk) > 0:
        cli = clicopy
        cli += ' switch %s trunk-delete name %s ' % (switch, trunk[0])
        if 'Success' in run_cli(module, cli):
            CHANGED_FLAG.append(True)
            return ' %s: Deleted %s trunk successfully \n' % (switch, trunk[0])


def assign_loopback_ip(module, loopback_address):
    """
    Method to add loopback interface to vrouters.
    :param module: The Ansible module to fetch input parameters.
    :param loopback_address: The loopback ip to be assigned.
    :return: String describing if loopback ips got assigned or not.
    """
    global CHANGED_FLAG
    output = ''
    address = loopback_address.split('.')
    static_part = str(address[0]) + '.' + str(address[1]) + '.'
    static_part += str(address[2]) + '.'

    cli = pn_cli(module)
    clicopy = cli
    switch_list = list(module.params['pn_spine_list'])
    switch_list += module.params['pn_leaf_list']

    vrouter_count = 1
    for switch in switch_list:
        vrouter = switch + '-vrouter'
        ip = static_part + str(vrouter_count)

        cli = clicopy
        cli += ' vrouter-loopback-interface-show ip ' + ip
        cli += ' format switch no-show-headers '
        existing_vrouter = run_cli(module, cli).split()

        if vrouter not in existing_vrouter:
            cli = clicopy
            cli += ' vrouter-loopback-interface-add vrouter-name '
            cli += vrouter
            cli += ' ip ' + ip
            run_cli(module, cli)
            output += ' %s: Added loopback ip %s to %s \n' % (
                switch, ip, vrouter
            )
            CHANGED_FLAG.append(True)
        else:
            output += ' %s: Loopback ip %s for %s already exists \n' % (
                switch, ip, vrouter
            )

        vrouter_count += 1

    return output


def auto_configure_link_ips(module):
    """
    Method to auto configure link IPs for layer3 fabric.
    :param module: The Ansible module to fetch input parameters.
    :return: String describing output of configuration.
    """
    spine_list = module.params['pn_spine_list']
    leaf_list = module.params['pn_leaf_list']
    fabric_loopback = module.params['pn_assign_loopback']
    supernet = module.params['pn_supernet']
    output = ''

    cli = pn_cli(module)
    clicopy = cli
    cli += ' fabric-node-show format name no-show-headers '
    switch_names = run_cli(module, cli).split()
    switch_names = list(set(switch_names))

    # Disable auto trunk on all switches.
    for switch in switch_names:
        modify_auto_trunk_setting(module, switch, 'disable')

    # Get the list of available link ips to assign.
    available_ips = calculate_link_ip_addresses(module.params['pn_net_address'],
                                                module.params['pn_cidr'],
                                                supernet, 2)

    # Get the fabric name and create vnet name required for vrouter creation.
    cli = clicopy
    cli += ' fabric-node-show format fab-name no-show-headers '
    fabric_name = list(set(run_cli(module, cli).split()))[0]
    vnet_name = str(fabric_name) + '-global'

    # Create vrouter on all switches.
    for switch in switch_names:
        output += create_vrouter(module, switch, vnet_name)

    for spine in spine_list:
        for leaf in leaf_list:
            cli = clicopy
            cli += ' switch %s port-show hostname %s ' % (leaf, spine)
            cli += ' format port no-show-headers '
            leaf_port = run_cli(module, cli).split()
            leaf_port = list(set(leaf_port))

            if 'Success' in leaf_port:
                continue

            while len(leaf_port) > 0:
                ip_list = available_ips.next()
                lport = leaf_port[0]
                ip = ip_list[0]
                delete_trunk(module, leaf, lport, spine)
                output += create_interface(module, leaf, ip, lport)

                leaf_port.remove(lport)

                ip = ip_list[1]

                cli = clicopy
                cli += ' switch %s port-show port %s ' % (leaf, lport)
                cli += ' format rport no-show-headers '
                rport = run_cli(module, cli).split()
                rport = list(set(rport))
                rport = rport[0]

                delete_trunk(module, spine, rport, leaf)
                output += create_interface(module, spine, ip, rport)

    if fabric_loopback:
        # Assign loopback ip to vrouters.
        output += assign_loopback_ip(module, module.params['pn_loopback_ip'])

    for switch in switch_names:
        # Enable auto trunk.
        modify_auto_trunk_setting(module, switch, 'enable')

    return output


def main():
    """ This section is for arguments parsing """
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=False, type='str'),
            pn_clipassword=dict(required=False, type='str', no_log=True),
            pn_net_address=dict(required=False, type='str'),
            pn_cidr=dict(required=False, type='str'),
            pn_supernet=dict(required=False, type='str'),
            pn_spine_list=dict(required=False, type='list'),
            pn_leaf_list=dict(required=False, type='list'),
            pn_update_fabric_to_inband=dict(required=False, type='bool',
                                            default=False),
            pn_assign_loopback=dict(required=False, type='bool', default=False),
            pn_loopback_ip=dict(required=False, type='str',
                                default='109.109.109.0/24'),
            pn_bfd=dict(required=False, type='bool', default=False),
            pn_bfd_min_rx=dict(required=False, type='str'),
            pn_bfd_multiplier=dict(required=False, type='str'),
            pn_stp=dict(required=False, type='bool', default=False),
        )
    )

    global CHANGED_FLAG

    # L3 setup (link ips)
    message = auto_configure_link_ips(module)

    # Update fabric network to in-band if flag is True
    if module.params['pn_update_fabric_to_inband']:
        message += update_fabric_network_to_inband(module)

    # Enable STP if flag is True
    if module.params['pn_stp']:
        message += modify_stp(module, 'enable')

    message_string = message
    results = []
    switch_list = module.params['pn_spine_list'] + module.params['pn_leaf_list']

    for switch in switch_list:
        replace_string = switch + ': '
        for line in message_string.splitlines():
            if replace_string in line:
                json_msg = {
                    'switch' : switch,
                    'output' : (line.replace(replace_string, '')).strip()
                }
                results.append(json_msg)

    # Exit the module and return the required JSON.
    module.exit_json(
        unreachable=False,
        msg='L3 ZTP configuration succeeded',
        summary=results,
        exception='',
        failed=False,
        changed=True if True in CHANGED_FLAG else False,
        task='Configure L3 ZTP'
    )


if __name__ == '__main__':
    main()
