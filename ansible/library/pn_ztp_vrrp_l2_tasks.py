#!/usr/bin/python
""" PN CLI VRRP L2 """

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
author: 'Pluribus Networks (@gauravbajaj)'
modified by: 'Pluribus Networks (@saptaktakalkar)'
version: 1
short_description: CLI command to configure VRRP - Layer 2 Setup
description: Virtual Router Redundancy Protocol (VRRP) - Layer 2 Setup
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
    pn_spine_list:
      description:
        - Specify list of Spine hosts
      required: False
      type: list
    pn_leaf_list:
      description:
        - Specify list of leaf hosts
      required: False
      type: list
    pn_vrrp_id:
      description:
        - Specify the vrrp id to be assigned.
      required: False
      default: '18'
      type: str
    pn_vrrp_ip:
      description:
        - Specify the vrrp ip to be assigned.
      required: False
      default: '18'
      type: str
    pn_active_switch:
      description:
        - Specify the name of the active switch..
      required: False
      type: str
    pn_vlan_range:
      description:
        - Specify the vlan range.
      required: False
      default: '100-200'
      type: str
    pn_vrrp_no_interface:
      description:
        - Specify the number of vrrp interfaces to create.
      required: False
      default: '100'
      type: str
"""

EXAMPLES = """
    - name: VRRP L2 setup
      pn_ztp_vrrp_l2_tasks:
        pn_cliusername: "{{ USERNAME }}"
        pn_clipassword: "{{ PASSWORD }}"
        pn_fabric_name: 'ztp-fabric'
        pn_spine_list: "{{ groups['spine'] }}"
        pn_leaf_list: "{{ groups['leaf'] }}"
        pn_vrrp_id: '18'
        pn_vrrp_ip: '101.101.$.0/24'
        pn_active_switch: 'auto-spine1'
        pn_vlan_range: '101-200'
        pn_vrrp_no_interface: '100'
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
    :param module: The Ansible module to fetch username, password and switch
    :return: The cli string for further processing
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


def create_vlan(module, start, end):
    """
    Method to create vlans
    :param module: The Ansible module to fetch input parameters.
    :param start: Start of the vlan range for vlans to be created.
    :param end: End of the vlan range for vlans to be created.
    :return: List of created vlans.
    """
    global CHANGED_FLAG
    vlan = []
    output = ''
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
            output += ' vlan with id ' + id_str + ' created! '
            CHANGED_FLAG.append(True)
        else:
            output += ' vlan with id ' + id_str + ' already exists! '
            CHANGED_FLAG.append(False)

        vlan_id += 1

    return vlan


def create_l2_vrouter(module, switch, vrrp_id):
    """
    Method to create vrouter and assign vrrp_id to the switches.
    :param module: The Ansible module to fetch input parameters.
    :param switch: The switch name on which vrouter will be created.
    :param vrrp_id: The vrrp_id to be assigned.
    :return: The output string informing details of vrouter created and
    interface added or if vrouter already exists.
    """
    global CHANGED_FLAG
    output = ''
    switch_temp = switch
    vrouter_name = switch_temp + '-vrouter'
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
        output += ' Created vrouter %s on switch %s! ' % (vrouter_name, switch)
        CHANGED_FLAG.append(True)
    else:
        output += ' Vrouter name %s on switch %s already exists! ' % (
            vrouter_name, switch)
        CHANGED_FLAG.append(False)

    return output


def create_l2_interface(module, switch, ip, vlan_id, vrrp_id, ip_count,
                        vrrp_priority):
    """
    Method to add vrouter interface and assign IP to it along with
    vrrp_id and vrrp_priority.
    :param module: The Ansible module to fetch input parameters.
    :param switch: The switch name on which vrouter will be created.
    :param ip: IP address to be assigned to vrouter interface.
    :param vlan_id: vlan_id to be assigned
    :param vrrp_id: vrrp id to be assigned.
    :param vrrp_priority: priority to be given(110 for active switch).
    :param ip_count: The value of fourth octet in the ip
    :return: The output string informing details of vrouter created and
    interface added or if vrouter already exists.
    """
    global CHANGED_FLAG
    output = ''
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
        output += ' Added vrouter interface with ip %s ' % ip2
        CHANGED_FLAG.append(True)
    else:
        output += ' Interface already exists for vrouter %s! ' % vrouter_name[0]
        CHANGED_FLAG.append(False)

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
        run_cli(module, cli)
        output += ' Added vrouter interface with ip %s ' % ip1
        CHANGED_FLAG.append(True)
    else:
        output += ' Interface already exists for vrouter %s! ' % vrouter_name[0]
        CHANGED_FLAG.append(False)

    return output


def configure_vrrp(module, vrrp_id, no_interface, vrrp_ip, active_switch,
                   vlan_range):
    """
    Method to configure VRRP.
    :param module: The Ansible module to fetch input parameters.
    :param vrrp_id: The vrrp_id need to be assigned.
    :param no_interface: The number of interfaces to be added.
    :param vrrp_ip: The vrrp_ip needed to be assigned.
    :param active_switch: The name of the active switch.
    :param vlan_range: The vlan_range for creating the vlans.
    :return: It returns the output of the configuration
    """
    output = ''
    spine_list = module.params['pn_spine_list']
    vlan_range_split = vlan_range.split('-')
    start = vlan_range_split[0]
    end_no_interface = int(start) + int(no_interface)
    vlan = create_vlan(module, start, end_no_interface)

    output += ' vlans starting with %s to %s created! ' % (
        str(start), str(end_no_interface))

    for spine in spine_list:
        output += create_l2_vrouter(module, spine, vrrp_id)

    vrrp_ip_segment = vrrp_ip.split('.')
    host_count = 1
    for spine in spine_list:
        host_count += 1
        if spine == active_switch:
            vrrp_priority = '110'
        else:
            vrrp_priority = '100'

        for vlan_id in vlan:
            ip = vrrp_ip_segment[0] + '.' + vrrp_ip_segment[1] + '.'
            ip += vlan_id + '.' + vrrp_ip_segment[3]
            output += create_l2_interface(module, spine, ip, vlan_id, vrrp_id,
                                          str(host_count), vrrp_priority)

    return output


def main():
    """ This section is for arguments parsing """

    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=False, type='str'),
            pn_clipassword=dict(required=False, type='str', no_log=True),
            pn_fabric_name=dict(required=True, type='str'),
            pn_spine_list=dict(required=False, type='list'),
            pn_leaf_list=dict(required=False, type='list'),
            pn_vrrp_id=dict(required=False, type='str', default='18'),
            pn_vrrp_ip=dict(required=False, type='str',
                            dafault='101.101.$.0/24'),
            pn_active_switch=dict(required=False, type='str'),
            pn_vlan_range=dict(required=False, type='str', default='101-200'),
            pn_vrrp_no_interface=dict(required=False, type='str', default='100')

        )
    )

    global CHANGED_FLAG
    CHANGED_FLAG = []
    message = configure_vrrp(module, module.params['pn_vrrp_id'],
                             module.params['pn_vrrp_no_interface'],
                             module.params['pn_vrrp_ip'],
                             module.params['pn_active_switch'],
                             module.params['pn_vlan_range'])

    module.exit_json(
        stdout=message,
        error='0',
        failed=False,
        msg='VRRP Layer 2 Setup completed successfully',
        changed=True if True in CHANGED_FLAG else False
    )


# AnsibleModule boilerplate
from ansible.module_utils.basic import AnsibleModule

if __name__ == '__main__':
    main()

