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

from ansible.module_utils.basic import AnsibleModule
import shlex

DOCUMENTATION = """
---
module: pn_ztp
author: 'Pluribus Networks (@saptaktakalkar)'
modified by: 'Pluribus Networks (@gauravbajaj)'
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
    pn_inband_ip:
      description:
        - Inband ips to be assigned to switches starting with this value.
      required: False
      default: 172.16.0.0/24.
      type: str
    pn_fabric_control_network:
      description:
        - Specify fabric control network as either mgmt or in-band.
      required: False
      type: str
      choices: ['mgmt', 'in-band']
      default: 'mgmt'
    pn_toggle_40g:
      description:
        - Flag to indicate if 40g ports should be converted to 10g ports or not.
      required: False
      default: True
      type: bool
    pn_current_switch:
      description:
        - Name of the switch on which this task is currently getting executed.
      required: False
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
    pn_static_setup:
      description:
        - Flag to indicate if static values should be assign to
        following switch setup params.
      required: False
      default: False
      type: bool
    pn_mgmt_ip:
      description:
        - Specify MGMT-IP value to be assign if pn_static_setup is True.
      required: False
      type: str
    pn_mgmt_ip_subnet:
      description:
        - Specify subnet mask for MGMT-IP value to be assign if
        pn_static_setup is True.
      required: False
      type: str
    pn_gateway_ip:
      description:
        - Specify GATEWAY-IP value to be assign if pn_static_setup is True.
      required: False
      type: str
    pn_dns_ip:
      description:
        - Specify DNS-IP value to be assign if pn_static_setup is True.
      required: False
      type: str
    pn_dns_secondary_ip:
      description:
        - Specify DNS-SECONDARY-IP value to be assign if pn_static_setup is True
      required: False
      type: str
    pn_domain_name:
      description:
        - Specify DOMAIN-NAME value to be assign if pn_static_setup is True.
      required: False
      type: str
    pn_ntp_server:
      description:
        - Specify NTP-SERVER value to be assign if pn_static_setup is True.
      required: False
      type: str
    pn_web_api:
      description:
        - Flag to enable web api.
      default: True
      type: bool
    pn_stp:
      description:
        - Flag to enable STP at the end.
      required: False
      default: False
      type: bool
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
    pn_fabric_name: ztp-fabric
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


CHANGED_FLAG = []


def pn_cli(module):
    """
    This method is to generate the cli portion to launch the Netvisor cli.
    It parses the username, password, switch parameters from module.
    :param module: The Ansible module to fetch username, password and switch.
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
    This method executes the cli command on the target node(s) and returns the
    output.
    :param module: The Ansible module to fetch input parameters.
    :param cli: the complete cli string to be executed on the target node(s).
    :return: Output/Error or Success message depending upon
    the response from cli.
    """
    cli = shlex.split(cli)
    rc, out, err = module.run_command(cli)

    if out:
        return out

    if err:
        module.exit_json(
            error='1',
            failed=True,
            stderr=err.strip(),
            msg='Operation Failed: ' + str(cli),
            changed=False
        )
    else:
        return 'Success'


def auto_accept_eula(module):
    """
    Method to accept the EULA when we first login to a new switch.
    :param module: The Ansible module to fetch input parameters.
    :return: The output of run_cli() method.
    """
    password = module.params['pn_clipassword']
    cli = ' /usr/bin/cli --quiet --skip-setup eula-show '
    cli = shlex.split(cli)
    rc, out, err = module.run_command(cli)

    if err:
        cli = '/usr/bin/cli --quiet'
        cli += ' --skip-setup --script-password '
        cli += ' switch-setup-modify password ' + password
        cli += ' eula-accepted true '
        return run_cli(module, cli)
    elif out:
        return ' EULA has been accepted already! '


def update_switch_names(module, switch_name):
    """
    Method to update switch names.
    :param module: The Ansible module to fetch input parameters.
    :param switch_name: Name to assign to the switch.
    :return: String describing switch name got modified or not.
    """
    cli = pn_cli(module)
    cli += ' switch-setup-show format switch-name '
    if switch_name in run_cli(module, cli).split()[1]:
        return ' Switch name is same as hostname! '
    else:
        cli = pn_cli(module)
        cli += ' switch-setup-modify switch-name ' + switch_name
        run_cli(module, cli)
        return ' Updated switch name to match hostname! '


def make_switch_setup_static(module):
    """
    Method to assign static values to different switch setup parameters.
    :param module: The Ansible module to fetch input parameters.
    """
    mgmt_ip = module.params['pn_mgmt_ip']
    mgmt_ip_subnet = module.params['pn_mgmt_ip_subnet']
    gateway_ip = module.params['pn_gateway_ip']
    dns_ip = module.params['pn_dns_ip']
    dns_secondary_ip = module.params['pn_dns_secondary_ip']
    domain_name = module.params['pn_domain_name']
    ntp_server = module.params['pn_ntp_server']

    if mgmt_ip:
        cli = pn_cli(module)
        ip = mgmt_ip + '/' + mgmt_ip_subnet
        cli += ' switch-setup-modify mgmt-ip ' + ip
        run_cli(module, cli)

    if gateway_ip:
        cli = pn_cli(module)
        cli += ' switch-setup-modify gateway-ip ' + gateway_ip
        run_cli(module, cli)

    if dns_ip:
        cli = pn_cli(module)
        cli += ' switch-setup-modify dns-ip ' + dns_ip
        run_cli(module, cli)

    if dns_secondary_ip:
        cli = pn_cli(module)
        cli += ' switch-setup-modify dns-secondary-ip ' + dns_secondary_ip
        run_cli(module, cli)

    if domain_name:
        cli = pn_cli(module)
        cli += ' switch-setup-modify domain-name ' + domain_name
        run_cli(module, cli)

    if ntp_server:
        cli = pn_cli(module)
        cli += ' switch-setup-modify ntp-server ' + ntp_server
        run_cli(module, cli)


def modify_stp_local(module, modify_flag):
    """
    Method to enable/disable STP (Spanning Tree Protocol) on a switch.
    :param module: The Ansible module to fetch input parameters.
    :param modify_flag: Enable/disable flag to set.
    :return: The output of run_cli() method.
    """
    cli = pn_cli(module)
    cli += ' switch-local stp-show format enable '
    current_state = run_cli(module, cli).split()[1]

    if current_state == 'yes':
        cli = pn_cli(module)
        cli += ' stp-modify ' + modify_flag
        return run_cli(module, cli)
    else:
        return ' STP is already disabled! '


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
    cli += ' fabric-node-show format name no-show-headers '
    switch_names = run_cli(module, cli).split()
    for switch in switch_names:
        cli = clicopy
        cli += ' switch %s stp-show format enable ' % switch
        current_state = run_cli(module, cli).split()[1]
        if current_state != 'yes':
            cli = clicopy
            cli += ' switch ' + switch
            cli += ' stp-modify ' + modify_flag
            output += run_cli(module, cli)
            output += ' '
        else:
            output += ' STP is already enabled! '

    return output


def configure_control_network(module, network):
    """
    Method to configure the fabric control network.
    :param module: The Ansible module to fetch input parameters.
    :param network: It can be in-band or management.
    :return: The output of run_cli() method.
    """
    cli = pn_cli(module)
    cli += ' fabric-info format control-network '
    current_control_network = run_cli(module, cli).split()[1]

    if current_control_network == network:
        return ' Fabric is already in %s control network ' % network
    else:
        cli = pn_cli(module)
        cli += ' fabric-local-modify control-network ' + network
        return run_cli(module, cli)


def enable_ports(module):
    """
    Method to enable all ports of a switch.
    :param module: The Ansible module to fetch input parameters.
    :return: The output of run_cli() method.
    """
    cli = pn_cli(module)
    cli += ' port-config-show format port no-show-headers '
    out = run_cli(module, cli)

    cli = pn_cli(module)
    cli += ' port-config-show format port speed 40g no-show-headers '
    out_40g = run_cli(module, cli)
    out_remove10g = []

    if len(out_40g) > 0 and out_40g != 'Success':
        out_40g = out_40g.split()
        out_40g = list(set(out_40g))
        if len(out_40g) > 0:
            for port_number in out_40g:
                out_remove10g.append(str(int(port_number) + int(1)))
                out_remove10g.append(str(int(port_number) + int(2)))
                out_remove10g.append(str(int(port_number) + int(3)))

    if out:
        out = out.split()
        out = set(out) - set(out_remove10g)
        out = list(out)
        if out:
            ports = ','.join(out)
            cli = pn_cli(module)
            cli += ' port-config-modify port %s enable ' % ports
            return run_cli(module, cli)
    else:
        return out


def create_fabric(module, fabric_name, fabric_network):
    """
    Method to create/join a fabric with default fabric type as mgmt.
    :param module: The Ansible module to fetch input parameters.
    :param fabric_name: Name of the fabric to create/join.
    :param fabric_network: Type of the fabric to create (mgmt/in-band).
    Default value: mgmt
    :return: The output of run_cli() method.
    """
    cli = pn_cli(module)
    clicopy = cli

    cli += ' fabric-show format name no-show-headers '
    fabrics_names = run_cli(module, cli).split()

    if fabric_name not in fabrics_names:
        cli = clicopy
        cli += ' fabric-create name ' + fabric_name
        cli += ' fabric-network ' + fabric_network
    else:
        cli = clicopy
        cli += ' fabric-info format name no-show-headers'
        cli = shlex.split(cli)
        rc, out, err = module.run_command(cli)

        if err:
            cli = clicopy
            cli += ' fabric-join name ' + fabric_name
        elif out:
            present_fabric_name = out.split()
            if present_fabric_name[1] not in fabrics_names:
                cli = clicopy
                cli += ' fabric-join name ' + fabric_name
            else:
                return 'Switch already in the fabric'

    return run_cli(module, cli)


def enable_web_api(module):
    """
    Method to enable web api on switches.
    :param module: The Ansible module to fetch input parameters.
    """
    cli = pn_cli(module)
    cli += ' admin-service-modify web if mgmt '
    run_cli(module, cli)


def update_fabric_network_to_inband(module):
    """
    Method to update fabric network type to in-band
    :param module: The Ansible module to fetch input parameters.
    :return: The output of run_cli() method.
    """
    output = ''
    cli = pn_cli(module)
    clicopy = cli
    cli += ' fabric-node-show format name no-show-headers '
    switch_names = run_cli(module, cli).split()
    for switch in switch_names:
        cli = clicopy
        cli += ' fabric-info format fabric-network '
        fabric_network = run_cli(module, cli).split()[1]
        if fabric_network != 'in-band':
            cli = clicopy
            cli += ' switch ' + switch
            cli += ' fabric-local-modify fabric-network in-band '
            output += run_cli(module, cli)
        else:
            output += ' Fabric network is already in-band! '

    return output


def calculate_link_ip_addresses(address_str, cidr_str, supernet_str):
    """
    Method to calculate link IPs for layer 3 fabric
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
    base_addr = int(address[3])
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
    diff = base_addr % (supernet_range + 2)
    host = base_addr - diff
    count, hostmin, hostmax = 0, 0, 0
    third_octet = network[2]
    available_ips = []
    while third_octet <= last_ip[2]:
        ips_list = []
        while count < last_ip[3]:
            hostmin = host + 1
            hostmax = hostmin + supernet_range - 1
            while hostmin <= hostmax:
                ips_list.append(hostmin)
                hostmin += 1
            host = hostmax + 2
            count = host

        list_index = 0
        ip_address = str(last_ip[0]) + '.' + str(last_ip[1]) + '.'
        ip_address += str(third_octet)
        while list_index < len(ips_list):
            ip = ip_address + '.' + str(ips_list[list_index]) + "/"
            ip += supernet_str
            available_ips.append(ip)
            list_index += 1

        host, count, hostmax, hostmin = 0, 0, 0, 0
        third_octet += 1

    return available_ips


def create_vrouter(module, switch):
    """
    Method to create vrouter.
    :param module: The Ansible module to fetch input parameters.
    :param switch: The switch name on which vrouter will be created.
    :return: The output string informing details of vrouter created.
    """
    switch_temp = switch
    vrouter_name = switch_temp + '-vrouter'
    vnet_name = module.params['pn_fabric_name'] + '-global'
    global CHANGED_FLAG

    cli = pn_cli(module)
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
        CHANGED_FLAG.append(True)
    else:
        output = ' Vrouter name %s on switch %s already exists! ' % (
            vrouter_name, switch)
        CHANGED_FLAG.append(False)

    return output + ' '


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
    vrouter_name = run_cli(module, cli).split()

    cli = clicopy
    cli += ' vrouter-interface-show l3-port %s ip %s ' % (port, ip)
    cli += ' format switch no-show-headers '
    existing_vrouter = run_cli(module, cli).split()
    existing_vrouter = list(set(existing_vrouter))

    if vrouter_name[0] not in existing_vrouter:
        cli = clicopy
        cli += ' vrouter-interface-add vrouter-name ' + vrouter_name[0]
        cli += ' ip ' + ip
        cli += ' l3-port ' + port
        run_cli(module, cli)
        output += ' Added vrouter interface with ip %s on %s! ' % (ip, switch)

        if module.params['pn_bfd']:
            cli = clicopy
            cli += ' vrouter-interface-show vrouter-name ' + vrouter_name[0]
            cli += ' l3-port %s format nic no-show-headers ' % port
            nic = run_cli(module, cli).split()[1]

            cli = clicopy
            cli += ' vrouter-interface-config-add '
            cli += ' vrouter-name %s nic %s ' % (vrouter_name[0], nic)
            cli += ' bfd-min-rx ' + module.params['pn_bfd_min_rx']
            cli += ' bfd-multiplier ' + module.params['pn_bfd_multiplier']
            run_cli(module, cli)
            output += ' Added BFD config to ' + vrouter_name[0]

        CHANGED_FLAG.append(True)
    else:
        output += ' Interface already exists on %s! ' % vrouter_name[0]
        CHANGED_FLAG.append(False)

    return output + ' '


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
    :param peer_switch: The port connecting the switch to another switch. This
    switch is peer_switch
    :return: The output of run_cli() method.
    """
    cli = pn_cli(module)
    clicopy = cli
    cli += ' switch %s port-show port %s hostname %s ' % (switch, switch_port,
                                                          peer_switch)
    cli += ' format trunk no-show-headers '
    trunk = run_cli(module, cli).split()
    trunk = list(set(trunk))
    if len(trunk) > 0:
        cli = clicopy
        cli += ' switch %s trunk-delete name %s ' % (switch, trunk[0])
        if 'Success' in run_cli(module, cli):
            CHANGED_FLAG.append(True)
            return ' Deleted %s trunk successfully! ' % trunk[0]
    else:
        CHANGED_FLAG.append(False)
        return ''


def assign_loopback_ip(module, loopback_address):
    """
    Method to add loopback interface to vrouter.
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
    cli += ' vrouter-show format name no-show-headers '
    vrouter_names = run_cli(module, cli).split()

    if len(vrouter_names) > 0:
        vrouter_count = 1
        if len(vrouter_names) + vrouter_count - 1 <= 255:
            for vrouter in vrouter_names:
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
                    output += ' Added loopback ip %s to %s! ' % (ip, vrouter)
                    CHANGED_FLAG.append(True)
                else:
                    output += ' Loopback ip %s for %s already exists! ' % (
                        ip, vrouter)
                    CHANGED_FLAG.append(False)

                vrouter_count += 1
        else:
            output += ' Not enough loopback ips available for all vrouters! '
            CHANGED_FLAG.append(False)
    else:
        output += ' No vrouters exists to assign loopback ips! '
        CHANGED_FLAG.append(False)

    return output


def auto_configure_link_ips(module):
    """
    Method to auto configure link IPs for layer3 fabric.
    :param module: The Ansible module to fetch input parameters.
    :return: The output of create_vrouter_and_interface() method.
    """
    spine_list = module.params['pn_spine_list']
    leaf_list = module.params['pn_leaf_list']
    fabric_loopback = module.params['pn_assign_loopback']
    address = module.params['pn_net_address']
    cidr = module.params['pn_cidr']
    supernet = module.params['pn_supernet']

    output = ''
    cli = pn_cli(module)
    clicopy = cli

    cli += ' fabric-node-show format name no-show-headers '
    switch_names = run_cli(module, cli).split()
    switch_names = list(set(switch_names))

    for switch in switch_names:
        modify_auto_trunk_setting(module, switch, 'disable')

    available_ips = calculate_link_ip_addresses(address, cidr, supernet)

    for switch in switch_names:
        output += create_vrouter(module, switch)

    for spine in spine_list:
        for leaf in leaf_list:
            cli = clicopy
            cli += ' switch %s port-show hostname %s' % (leaf, spine)
            cli += ' format port no-show-headers '
            leaf_port = run_cli(module, cli).split()

            while len(leaf_port) > 0:
                lport = leaf_port[0]
                ip = available_ips[0]
                delete_trunk(module, leaf, lport, spine)
                output += create_interface(module, leaf, ip, lport)

                leaf_port.remove(lport)
                available_ips.remove(ip)
                ip = available_ips[0]

                cli = clicopy
                cli += ' switch %s port-show port %s ' % (leaf, lport)
                cli += ' format rport no-show-headers '
                sport = run_cli(module, cli)

                delete_trunk(module, spine, sport, leaf)
                output += create_interface(module, spine, ip, sport)
                available_ips.remove(ip)

                ip_count = 0
                diff = 32 - int(supernet)
                count = (1 << diff) - 4
                while ip_count < count:
                    available_ips.pop(0)
                    ip_count += 1

    if fabric_loopback:
        loopback_address = module.params['pn_loopback_ip']
        output += assign_loopback_ip(module, loopback_address)

    for switch in switch_names:
        modify_auto_trunk_setting(module, switch, 'enable')

    return output


def create_cluster(module, switch, name, node1, node2):
    """
    Method to create a cluster between two switches.
    :param module: The Ansible module to fetch input parameters.
    :param switch: Name of the local switch.
    :param name: The name of the cluster to create.
    :param node1: First node of the cluster.
    :param node2: Second node of the cluster.
    :return: The output of run_cli() method.
    """
    global CHANGED_FLAG
    cli = pn_cli(module)
    clicopy = cli
    cli += ' switch %s cluster-show format name no-show-headers ' % node1
    cluster_list = run_cli(module, cli).split()
    if name not in cluster_list:
        cli = clicopy
        cli += ' switch %s cluster-create name %s ' % (switch, name)
        cli += ' cluster-node-1 %s cluster-node-2 %s ' % (node1, node2)
        if 'Success' in run_cli(module, cli):
            CHANGED_FLAG.append(True)
            return ' %s created successfully! ' % name
    else:
        CHANGED_FLAG.append(False)
        return ' %s already exists! ' % name


def get_ports(module, switch, peer_switch):
    """
    Method to figure out connected ports between two switches.
    :param module: The Ansible module to fetch input parameters.
    :param switch: Name of the local switch.
    :param peer_switch: Name of the connected peer switch.
    :return: List of connected ports.
    """
    cli = pn_cli(module)
    cli += ' switch %s port-show hostname %s' % (switch, peer_switch)
    cli += ' format port no-show-headers '
    return run_cli(module, cli).split()


def create_trunk(module, switch, name, ports):
    """
    Method to create a trunk on a switch.
    :param module: The Ansible module to fetch input parameters.
    :param switch: Name of the local switch.
    :param name: The name of the trunk to create.
    :param ports: List of connected ports.
    :return: The output of run_cli() method.
    """
    global CHANGED_FLAG
    cli = pn_cli(module)
    clicopy = cli
    cli += ' switch %s trunk-show format name no-show-headers ' % switch
    trunk_list = run_cli(module, cli).split()
    if name not in trunk_list:
        cli = clicopy
        ports_string = ','.join(ports)
        cli += ' switch %s trunk-create name %s ' % (switch, name)
        cli += ' ports %s ' % ports_string
        if 'Success' in run_cli(module, cli):
            CHANGED_FLAG.append(True)
            return ' %s trunk created successfully! ' % name
    else:
        CHANGED_FLAG.append(False)
        return ' %s trunk already exists! ' % name


def find_non_cluster_leafs(module, leaf_list):
    """
    Method to find leafs which are not part of any cluster.
    :param module: The Ansible module to fetch input parameters.
    :param leaf_list: The list of leaf switches.
    :return: List of non clustered leaf switches.
    """
    cli = pn_cli(module)
    non_cluster_leafs = []
    clicopy = cli
    clicopy += ' cluster-show format cluster-node-1 no-show-headers '
    cluster1 = run_cli(module, clicopy).split()

    clicopy = cli
    clicopy += ' cluster-show format cluster-node-2 no-show-headers '
    cluster2 = run_cli(module, clicopy).split()

    for leaf in leaf_list:
        if (leaf not in cluster1) and (leaf not in cluster2):
            non_cluster_leafs.append(leaf)

    return non_cluster_leafs


def create_vlag(module, switch, name, peer_switch, port, peer_port):
    """
    Method to create virtual link aggregation groups.
    :param module: The Ansible module to fetch input parameters.
    :param switch: Name of the local switch.
    :param name: The name of the vlag to create.
    :param port: List of local switch ports.
    :param peer_switch: Name of the peer switch.
    :param peer_port: List of peer switch ports.
    :return: The output of run_cli() method.
    """
    global CHANGED_FLAG
    cli = pn_cli(module)
    clicopy = cli
    cli += ' switch %s vlag-show format name no-show-headers ' % switch
    vlag_list = run_cli(module, cli).split()
    if name not in vlag_list:
        cli = clicopy
        cli += ' switch %s vlag-create name %s port %s ' % (switch, name, port)
        cli += ' peer-switch %s peer-port %s mode active-active' % (peer_switch,
                                                                    peer_port)
        if 'Success' in run_cli(module, cli):
            CHANGED_FLAG.append(True)
            return ' %s vlag configured successfully! ' % name
    else:
        CHANGED_FLAG.append(False)
        return ' %s vlag is already configured! ' % name


def create_trunk_vlag(module, node1, dest_list):
    """
    The method is aggregation of create_trunk() and get_ports()
    to create a trunk
    :param module: The Ansible module to fetch input parameters.
    :param node1: The local node from which lag needs to be created.
    :param dest_list: The list of destination to know the physical links port.
    :return: It returns the name of the trunk created.
    """
    string2 = ''
    src_ports = []
    for node in dest_list:
        src_ports += get_ports(module, node1, node)
        string2 += str(node)

    src_ports = list(set(src_ports))
    name = node1 + '-to-' + string2
    create_trunk(module, node1, name, src_ports)
    return name


def create_cluster_trunk_vlag(module, non_cluster_leaf, spine_list):
    """
    Method to create clusters, trunks and vlag for the switches having
    physical links.
    :param module: The Ansible module to fetch input parameters.
    :param non_cluster_leaf: The list of non clustered leaf switches.
    :param spine_list: The list of spine switches.
    :return: The output message related to vlag, lag and cluster creation.
    """
    cli = pn_cli(module)
    clicopy = cli
    output = ' '
    flag = 0
    while flag == 0:
        if len(non_cluster_leaf) == 0:
            flag += 1
        else:
            node1 = non_cluster_leaf[0]
            non_cluster_leaf.remove(node1)

            cli = clicopy
            cli += ' switch %s lldp-show ' % node1
            cli += ' format sys-name no-show-headers '
            system_names = run_cli(module, cli).split()
            system_names = list(set(system_names))

            cli = clicopy
            cli += ' switch %s fabric-node-show ' % node1
            cli += ' format name no-show-headers '
            nodes_in_fabric = run_cli(module, cli).split()
            nodes_in_fabric = list(set(nodes_in_fabric))

            for system in system_names:
                if system not in nodes_in_fabric:
                    system_names.remove(system)

            flag1 = 0
            node_count = 0
            while (node_count < len(system_names)) and (flag1 == 0):
                node2 = system_names[node_count]
                if node2 not in spine_list:
                    if node2 in non_cluster_leaf:
                        name = node1 + '-to-' + node2 + '-cluster'
                        output += create_cluster(module, node2, name,
                                                 node1, node2)

                        non_cluster_leaf.remove(node2)
                        name1 = create_trunk_vlag(module, node1, spine_list)
                        name2 = create_trunk_vlag(module, node2, spine_list)

                        name = node1 + node2 + '-to-' + 'spine'
                        output += create_vlag(module, node1, name, node2,
                                              name1, name2)

                        list1 = [node1, node2]
                        spine1 = str(spine_list[0])
                        spine2 = str(spine_list[1])
                        name1 = create_trunk_vlag(module, spine1, list1)
                        name2 = create_trunk_vlag(module, spine2, list1)
                        name = spine1 + spine2 + '-to-' + node1 + node2
                        output += create_vlag(module, spine1, name, spine2,
                                              name1, name2)
                        flag1 += 1
                    else:
                        print ' Switch is already part of a cluster '
                else:
                    print ' Switch is spine '

                node_count += 1
    return output


def create_non_cluster_leaf_vlag(module, non_cluster_leaf, spine_list):
    """
    Method to create lag and vlag for non clustered leafs.
    :param module: The Ansible module to fetch input parameters.
    :param non_cluster_leaf: The list of all non cluster leaf swicthes.
    :param spine_list: The list of all spine switches.
    :return: The output messages related to vlag creation.
    """
    output = ' '
    for leaf in non_cluster_leaf:
        create_trunk_vlag(module, leaf, spine_list)
        list1 = [leaf]
        spine1 = str(spine_list[0])
        spine2 = str(spine_list[1])
        name1 = create_trunk_vlag(module, spine1, list1)
        name2 = create_trunk_vlag(module, spine2, list1)

        name = spine1 + spine2 + '-to-' + leaf
        output += create_vlag(module, spine1, name, spine2, name1, name2)

    return output


def configure_auto_vlag(module):
    """
    Method to create and configure vlag.
    :param module: The Ansible module to fetch input parameters.
    :return: The output of run_cli() method.
    """
    output = ' '
    spine_list = module.params['pn_spine_list']
    leaf_list = module.params['pn_leaf_list']
    spine1 = spine_list[0]
    spine2 = spine_list[1]
    output += create_cluster(module, spine1, 'spine-cluster', spine1, spine2)
    non_cluster_leaf = find_non_cluster_leafs(module, leaf_list)
    output += create_cluster_trunk_vlag(module, non_cluster_leaf, spine_list)
    output += ' '
    non_cluster_leaf = find_non_cluster_leafs(module, leaf_list)
    output += create_non_cluster_leaf_vlag(module, non_cluster_leaf, spine_list)
    output += ' '
    return output


def toggle_40g_local(module):
    """
    Method to toggle 40g ports to 10g ports.
    :param module: The Ansible module to fetch input parameters.
    :return: The output messages for assignment.
    """
    output = ''
    cli = pn_cli(module)
    clicopy = cli
    cli += ' switch-local lldp-show format local-port no-show-headers '
    local_ports = run_cli(module, cli).split()

    cli = clicopy
    cli += ' switch-local port-config-show speed 40g '
    cli += ' format port no-show-headers '
    ports_40g = run_cli(module, cli)
    if len(ports_40g) > 0 and ports_40g != 'Success':
        ports_40g = ports_40g.split()
        ports_to_modify = list(set(ports_40g) - set(local_ports))

        for port in ports_to_modify:
            end_port = int(port) + 4
            range_port = port + '-' + str(end_port)

            cli = clicopy
            cli += ' switch-local port-config-modify port %s ' % range_port
            cli += ' speed disable '
            output += 'port range_port ' + range_port + ' disabled'
            output += run_cli(module, cli)

            cli = clicopy
            cli += ' switch-local port-config-modify port %s ' % range_port
            cli += ' speed 10g '
            output += 'port range_port ' + range_port + ' 10g converted'
            output += run_cli(module, cli)

            cli = clicopy
            cli += ' switch-local port-config-modify port %s ' % range_port
            cli += ' enable '
            output += 'port range_port ' + range_port + '  enabled'
            output += run_cli(module, cli)

    return output


def assign_inband_ip(module, inband_address):
    """
    Method to assign in-band ips to switches.
    :param module: The Ansible module to fetch input parameters.
    :param inband_address: The network ip for the in-band ips.
    :return: The output messages for assignment.
    """
    output = ''
    address = inband_address.split('.')
    static_part = str(address[0]) + '.' + str(address[1]) + '.'
    static_part += str(address[2]) + '.'
    last_octet = str(address[3]).split('/')
    subnet = last_octet[1]

    cli = pn_cli(module)
    clicopy = cli
    cli += ' fabric-node-show format name no-show-headers '
    switch_names = run_cli(module, cli).split()
    switch_names.sort()

    if len(switch_names) > 0:
        ip_count = 1
        if len(switch_names) + ip_count - 1 <= 255:
            for switch in switch_names:
                ip = static_part + str(ip_count) + '/' + subnet
                cli = clicopy
                cli += ' switch %s switch-setup-modify ' % switch
                cli += ' in-band-ip ' + ip
                if 'Success' in run_cli(module, cli):
                    output += ' Assigned in-band ips to ' + switch

                ip_count += 1
        else:
            output += ' Not enough in-band ips available for all the switches '
    else:
        output += ' No switches present '

    return output


def main():
    """ This section is for arguments parsing """
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=False, type='str'),
            pn_clipassword=dict(required=False, type='str', no_log=True),
            pn_fabric_name=dict(required=True, type='str'),
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
            pn_leaf_list=dict(required=False, type='list'),
            pn_update_fabric_to_inband=dict(required=False, type='bool',
                                            default=False),
            pn_assign_loopback=dict(required=False, type='bool', default=False),
            pn_loopback_ip=dict(required=False, type='str',
                                default='109.109.109.0/24'),
            pn_inband_ip=dict(required=False, type='str',
                              default='172.16.0.0/24'),
            pn_fabric_control_network=dict(required=False, type='str',
                                           choices=['mgmt', 'in-band'],
                                           default='mgmt'),
            pn_toggle_40g=dict(required=False, type='bool', default=True),
            pn_current_switch=dict(required=False, type='str'),
            pn_bfd=dict(required=False, type='bool', default=False),
            pn_bfd_min_rx=dict(required=False, type='str'),
            pn_bfd_multiplier=dict(required=False, type='str'),
            pn_static_setup=dict(required=False, type='bool', default=False),
            pn_mgmt_ip=dict(required=False, type='str'),
            pn_mgmt_ip_subnet=dict(required=False, type='str'),
            pn_gateway_ip=dict(required=False, type='str'),
            pn_dns_ip=dict(required=False, type='str'),
            pn_dns_secondary_ip=dict(required=False, type='str'),
            pn_domain_name=dict(required=False, type='str'),
            pn_ntp_server=dict(required=False, type='str'),
            pn_web_api=dict(type='bool', default=True),
            pn_stp=dict(required=False, type='bool', default=False),
        )
    )

    fabric_name = module.params['pn_fabric_name']
    fabric_network = module.params['pn_fabric_network']
    fabric_type = module.params['pn_fabric_type']
    run_l2_l3 = module.params['pn_run_l2_l3']
    control_network = module.params['pn_fabric_control_network']
    update_fabric_to_inband = module.params['pn_update_fabric_to_inband']
    inband_address = module.params['pn_inband_ip']
    toggle_40g_flag = module.params['pn_toggle_40g']
    current_switch = module.params['pn_current_switch']
    message = ' '
    global CHANGED_FLAG
    CHANGED_FLAG = []

    if not run_l2_l3:
        # Auto accept EULA
        eula_out_msg = auto_accept_eula(module)
        if 'Setup completed successfully' in eula_out_msg:
            message += ' EULA accepted on %s! ' % current_switch
            CHANGED_FLAG.append(True)
        else:
            message += eula_out_msg
            CHANGED_FLAG.append(False)

        # Update switch names to match host names from hosts file
        if 'Updated' in update_switch_names(module, current_switch):
            CHANGED_FLAG.append(True)
        else:
            CHANGED_FLAG.append(False)

        # Make switch setup static
        if module.params['pn_static_setup']:
            make_switch_setup_static(module)

        # Create/join fabric
        if 'already in the fabric' in create_fabric(module, fabric_name,
                                                    fabric_network):
            message += ' %s is already in fabric %s! ' % (current_switch,
                                                          fabric_name)
            CHANGED_FLAG.append(False)
        else:
            message += ' %s has joined fabric %s! ' % (current_switch,
                                                       fabric_name)
            CHANGED_FLAG.append(True)

        # Configure fabric control network to either mgmt or in-band
        net_out_msg = configure_control_network(module, control_network)
        if 'Success' in net_out_msg:
            message += ' Configured fabric control network to %s on %s! ' % (
                control_network, current_switch)
            CHANGED_FLAG.append(True)
        else:
            message += net_out_msg
            CHANGED_FLAG.append(False)

        # Enable web api if flag is True
        if module.params['pn_web_api']:
            enable_web_api(module)

        # Disable STP
        stp_out_msg = modify_stp_local(module, 'disable')
        if 'Success' in stp_out_msg:
            message += ' STP disabled on %s! ' % current_switch
            CHANGED_FLAG.append(True)
        else:
            message += stp_out_msg
            CHANGED_FLAG.append(False)

        # Enable ports
        ports_out_msg = enable_ports(module)
        if 'Success' in ports_out_msg:
            message += ' Ports enabled on %s! ' % current_switch
            CHANGED_FLAG.append(True)
        else:
            message += ports_out_msg
            CHANGED_FLAG.append(False)

        # Toggle 40g ports to 10g
        if toggle_40g_flag:
            if toggle_40g_local(module):
                message += ' Toggled 40G ports to 10G on %s! ' % current_switch
                CHANGED_FLAG.append(True)
            else:
                CHANGED_FLAG.append(False)

    else:
        # Assign in-band ips
        message += assign_inband_ip(module, inband_address)

        if fabric_type == 'layer2':
            # L2 setup (auto-vlag)
            message += configure_auto_vlag(module)

        if fabric_type == 'layer3':
            # L3 setup (link ips)
            message += auto_configure_link_ips(module)

        # Update fabric network to in-band if flag is True
        if update_fabric_to_inband:
            if 'Success' in update_fabric_network_to_inband(module):
                message += ' Updated fabric network to in-band! '
                CHANGED_FLAG.append(True)
            else:
                message += ' Fabric network is already in-band! '
                CHANGED_FLAG.append(False)

        # Enable STP if flag is True
        if module.params['pn_stp']:
            stp_out_msg = modify_stp(module, 'enable')
            if 'Success' in stp_out_msg:
                message += ' STP enabled! '
                CHANGED_FLAG.append(True)
            else:
                message += ' STP is already enabled! '
                CHANGED_FLAG.append(False)

    # Exit the module and return the required JSON
    module.exit_json(
        stdout=message,
        error='0',
        failed=False,
        msg='ZTP Configured Successfully.',
        changed=True if True in CHANGED_FLAG else False
    )


if __name__ == '__main__':
    main()

