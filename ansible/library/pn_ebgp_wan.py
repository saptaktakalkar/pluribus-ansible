#!/usr/bin/python
""" PN CLI Zero Touch Provisioning (ZTP) with EBGP(wan switches)"""

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
module: pn_ebgp_wan
author: 'Pluribus Networks (devops@pluribusnetworks.com)'
short_description: CLI command to do zero touch provisioning with ebgp.
description:
    Zero Touch Provisioning (ZTP) allows you to provision new switches in your
    network automatically, without manual intervention.
    It performs following steps:
        EBGP:
          - Assigning bgp_as
          - Configuring bgp_redistribute
          - Configuring bgp_maxpath
          - Assign ebgp_neighbor
          - Assign router_id
          - Create leaf_cluster
          - Add iBGP neighbor for clustered leaf
        OSPF:
          - Assign ospf_neighbor
          - Assign ospf_redistribute
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
    pn_wan_list:
      description:
        - Specify list of wan hosts
      required: False
      type: list
    pn_wan_bgp_as:
      description:
        - Specify bgp_as value to be added to vrouter.
      required: False
      type: str
      default: '75000'
    pn_ibgp_ip_range:
      description:
        - Specify ip range for ibgp interface.
      required: False
      type: str
      default: '75.75.75.0/30'
    pn_ibgp_vlan:
      description:
        - Specify vlan for ibgp interface.
      required: False
      type: str
      default: '4040'
    pn_bfd:
      description:
        - Specify bfd flag for the ebgp neighbor.
      required: False
      type: bool
      default: False
    pn_ospf_area_id:
      description:
        - Specify area_id value to be added to vrouter for ospf.
      required: False
      type: str
      default: '0'
"""

EXAMPLES = """
    - name: Configure eBGP/OSPF
      pn_ebgp_ospf:
        pn_cliusername: "{{ USERNAME }}"
        pn_clipassword: "{{ PASSWORD }}"
        pn_wan_list: "{{ groups['wan'] }}"
"""

RETURN = """
stdout:
  description: The set of responses for each command.
  returned: always
  type: str
changed:
  description: Indicates whether the CLI caused changes on the target.
  returned: always
  type: bool
failed:
  description: Indicates whether or not the execution failed on the target.
  returned: always
  type: bool
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


def add_bgp_as(module):
    """
    Method to add bgp_redistribute to the vrouter.
    :param module: The Ansible module to fetch input parameters.
    :return: String describing if bgp-redistribute got added or not.
    """
    global CHANGED_FLAG
    output = ''
    cli = pn_cli(module)
    clicopy = cli
    wan_bgp_as = module.params['pn_wan_bgp_as']

    for switch in module.params['pn_wan_switch_list']:
        cli = clicopy
        cli += ' vrouter-show location %s' % switch
        cli += ' format name no-show-headers'
        vrouter = run_cli(module, cli).split()[0]

        cli = clicopy
        cli += ' vrouter-modify name %s bgp-as %s ' % (vrouter,
                                                            wan_bgp_as)
        if 'Success' in run_cli(module, cli):
            output += ' %s: Added %s BGP_AS to %s \n' % (switch, wan_bgp_as,
                                                                   vrouter)
            CHANGED_FLAG.append(True)

    return output


def create_interface(module, switch, ip, port, vrouter):
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

    cli += ' vrouter-interface-show l3-port %s ip %s ' % (port, ip)
    cli += ' format switch no-show-headers '
    existing_vrouter = run_cli(module, cli).split()
    existing_vrouter = list(set(existing_vrouter))

    if vrouter not in existing_vrouter:
        # Add vrouter interface.
        cli = clicopy
        cli += ' vrouter-interface-add vrouter-name ' + vrouter
        cli += ' ip ' + ip
        cli += ' l3-port ' + port
        run_cli(module, cli)
        output += ' %s: Added vrouter interface with ip %s on %s \n' % (
            switch, ip, vrouter
        )

        CHANGED_FLAG.append(True)
    else:
        output += ' %s: Vrouter interface %s already exists on %s \n' % (
            switch, ip, vrouter
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

    if len(trunk) > 0 and 'Success' not in trunk:
        cli = clicopy
        cli += ' switch %s trunk-delete name %s ' % (switch, trunk[0])
        if 'Success' in run_cli(module, cli):
            CHANGED_FLAG.append(True)
            return ' %s: Deleted %s trunk successfully \n' % (switch, trunk[0])


def add_wan_ibgp_interface(module):
    """
    Method to create vrouter interface and add ebgp neighbor for wan switches.
    :param module: The Ansible module to fetch input parameters.
    :return: The output string informing details of vrouter created and
    """
    cli = pn_cli(module)
    clicopy = cli

    bgp_as = module.params['pn_wan_bgp_as']
    wan_switch_list = module.params['pn_wan_switch_list']
    ip = module.params['pn_wan_ip']

    output = ''

    ip = ip.split('/')[0]
    ip = ip.split('.')
    static_part = ip[0] + '.' + ip[1] + '.' + ip[2] + '.'
    network_count = 0
    subnet = 4

    # Disable auto trunk on all switches.
    for switch in wan_switch_list:
        modify_auto_trunk_setting(module, switch, 'disable')

    while len(wan_switch_list) > 1:
        wan_switch = wan_switch_list[0]
        wan_switch_list.remove(wan_switch)
        host_list = wan_switch_list

        cli = clicopy
        cli += ' vrouter-show location %s format name no-show-headers ' % wan_switch
        vrouter_switch1 = run_cli(module, cli).split()[0]

        for host_switch in host_list:

            cli = clicopy
            cli += ' vrouter-show location %s format name no-show-headers ' % host_switch
            vrouter_switch2 = run_cli(module, cli).split()[0]

            cli = clicopy
            cli += ' switch %s port-show hostname %s ' % (wan_switch, host_switch)
            cli += ' format port no-show-headers '
            port_list = run_cli(module, cli).split()
        
            while len(port_list) > 0 and 'Success' not in port_list:
        
                network = network_count * subnet
                lport = port_list[0]
        
                ip1 = static_part + str(int(network) + 1)
                ip2 = static_part + str(int(network) + 2)
                ip1_interface = ip1 + '/30'
                ip2_interface = ip2 + '/30'

                delete_trunk(module, wan_switch, lport, host_switch)
                output += create_interface(module, wan_switch, ip1_interface, lport, vrouter_switch1)
                port_list.remove(lport)
        
                cli = clicopy
                cli += ' switch %s port-show port %s ' % (wan_switch, lport)
                cli += ' format rport no-show-headers '
                rport = run_cli(module, cli).split()[0]
        
                delete_trunk(module, host_switch, rport, wan_switch)
                output += create_interface(module, host_switch, ip2_interface, rport, vrouter_switch2)
        
                cli = clicopy
                cli += ' vrouter-bgp-show remote-as ' + bgp_as
                cli += ' neighbor %s format switch no-show-headers ' % (
                    ip2)
                already_added = run_cli(module, cli).split()
        
                if vrouter_switch1 in already_added:
                    output += ' %s: ' % wan_switch
                    output += 'BGP Neighbor %s already exists for %s \n' % (
                        ip2, vrouter_switch1
                    )
                else:
                    cli = clicopy
                    cli += ' vrouter-bgp-add vrouter-name ' + vrouter_switch1
                    cli += ' neighbor %s remote-as %s ' % (ip2,
                                                           bgp_as)
        
                    if 'Success' in run_cli(module, cli):
                        output += ' %s: Added BGP Neighbor %s for %s \n' % (
                            wan_switch, ip2, vrouter_switch1
                        )
                        CHANGED_FLAG.append(True)
        
                cli = clicopy
                cli += ' vrouter-bgp-show remote-as ' + bgp_as
                cli += ' neighbor %s format switch no-show-headers ' % (
                    ip1)
                already_added = run_cli(module, cli).split()
        
                if vrouter_switch2 in already_added:
                    output += ' %s: ' % host_switch
                    output += 'BGP Neighbor %s already exists for %s \n' % (
                        ip1, vrouter_switch2
                    )
                else:
                    cli = clicopy
                    cli += ' vrouter-bgp-add vrouter-name ' + vrouter_switch2
                    cli += ' neighbor %s remote-as %s ' % (ip1,
                                                           bgp_as)
        
                    if 'Success' in run_cli(module, cli):
                        output += ' %s: Added BGP Neighbor %s for %s \n' % (
                            host_switch, ip1, vrouter_switch2
                        )
                        CHANGED_FLAG.append(True)
        
                network_count += 1
    return output


def create_vrouter_command(module, switch, vnet_name):
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
        run_cli(module, cli)
        CHANGED_FLAG.append(True)
        return ' %s: Created vrouter with name %s \n' % (switch, vrouter_name)
    else:
        return ' %s: Vrouter with name %s already exists \n' % (switch,
                                                                vrouter_name)


def create_vrouter(module):
    # Get the fabric name and create vnet name required for vrouter creation.
    cli = pn_cli(module)
    output = ''

    cli += ' fabric-node-show format fab-name no-show-headers '
    fabric_name = list(set(run_cli(module, cli).split()))[0]
    vnet_name = str(fabric_name) + '-global'

    # Create vrouter on all switches.
    for switch in module.params['pn_wan_switch_list']:
        output += create_vrouter_command(module, switch, vnet_name)


def main():
    """ This section is for arguments parsing """
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=False, type='str'),
            pn_clipassword=dict(required=False, type='str', no_log=True),
            pn_wan_switch_list=dict(required=False, type='list'),
            pn_wan_bgp_as=dict(required=False, type='str', default='75000'),
            pn_wan_ip=dict(required=False, type='str',
                                  default='85.75.75.0/24'),
        )
    )

    global CHANGED_FLAG

    message = create_vrouter(module)
    message = add_bgp_as(module)
    message += add_wan_ibgp_interface(module)

    module.exit_json(
        stdout=message,
        error='0',
        failed=False,
        changed=True if True in CHANGED_FLAG else False
    )


if __name__ == '__main__':
    main()

