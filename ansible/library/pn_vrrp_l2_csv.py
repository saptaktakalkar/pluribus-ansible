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
author: "Pluribus Networks (@gauravbajaj)"
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
    pn_csv_data:
      description:
        - String containing vrrp data parsed from csv file.
      required: False
      type: str
"""

EXAMPLES = """
    - name: VRRP L2 setup
      pn_ztp_vrrp_l2_csv:
        pn_cliusername: "{{ USERNAME }}"
        pn_clipassword: "{{ PASSWORD }}"
        pn_fabric_name: 'ztp-fabric'
        pn_spine_list: "{{ groups['spine'] }}"
        pn_leaf_list: "{{ groups['leaf'] }}"
        pn_vrrp_id: '18'
        pn_csv_data: "{{ lookup('file', '{{ csv_file }}') }}"
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
    :return: Output/Error or Success msg depending upon the response from cli.
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


def create_vlan(module, vlan_id):
    """
    This method is to create vlans.
    :param module: The Ansible module to fetch input parameters.
    :param vlan_id: vlan number to be created.
    :return: Success or failure message for the vlan.
    """
    output = ' '
    cli = pn_cli(module)
    clicopy = cli

    clicopy += ' vlan-show format id no-show-headers '
    already_vlan_id = run_cli(module, clicopy).split()
    already_vlan_id = list(set(already_vlan_id))

    id_str = str(vlan_id)
    if id_str not in already_vlan_id:
        clicopy = cli
        clicopy += ' vlan-create id '
        clicopy += id_str
        clicopy += ' scope fabric '
        output += run_cli(module, clicopy)
        output += 'vlan ' + vlan_id + ' created'
        output += "\n"
    else:
        output += 'vlan ' + vlan_id + ' already present'
        output += "\n"

    return output


def create_l2_vrouter(module, switch, vrrp_id):
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
        output += ' Created vrouter %s on switch %s ' % (vrouter_name, switch)
    else:
        output += ' Vrouter name %s on switch %s already exists. ' % (
            vrouter_name, switch)

    return output


def create_l2_interface(module, switch, ip, vlan_id, vrrp_id, ip_count,
                        vrrp_priority):
    """
    This method is to add vrouter interface and assign IP to it along with
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
        output += ' interface already exists for vrouter %s ' % vrouter_name[0]

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


def configure_vrrp(module, vrrp_id, vrrp_ip, active_switch, vlan_id):
    """
    This method is to configure vrrp.
    :param module: The Ansible module to fetch input parameters.
    :param vrrp_id: The vrrp_id need to be assigned.
    :param vrrp_ip: The vrrp_ip needed to be assigned.
    :param active_switch: The name of the active switch.
    :param vlan_id: The vlan_id to be assigned.
    :return: Output of the created vrrp configuration.
    """
    spine_list = module.params['pn_spine_list']
    output = create_vlan(module, vlan_id)
    host_count = 1
    for spine in spine_list:
        host_count += 1
        if spine == active_switch:
            vrrp_priority = '110'
        else:
            vrrp_priority = '100'

        output += create_l2_interface(module, spine, vrrp_ip, vlan_id, vrrp_id,
                                      str(host_count), vrrp_priority)
    return output


def configure_vrrp_l2(module, csv_data, vrrp_id):
    """
    This method is to configure VRRP L2.
    :param module: The Ansible module to fetch input parameters.
    :param csv_data: CSV data describing different vrrp attributes.
    :param vrrp_id: The vrrp id to be assigned.
    :return: Output of created vrrp configuration.
    """
    output = ' '
    spine_list = module.params['pn_spine_list']

    for switch in spine_list:
        output += create_l2_vrouter(module, switch, vrrp_id)
        output += ' '

    csv_data = csv_data.replace(" ", "")
    csv_data_list = csv_data.split('\n')
    for row in csv_data_list:
        elements = row.split(',')
        vrrp_ip = elements[0]
        vlan_id = elements[1]
        active_switch = str(elements[2])
        output += configure_vrrp(module, vrrp_id, vrrp_ip, active_switch,
                                 vlan_id)

    return output


def main():
    """ This section is for arguments parsing """
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=False, type='str'),
            pn_clipassword=dict(required=False, type='str', no_log=True),
            pn_cliswitch=dict(required=False, type='str'),
            pn_fabric_name=dict(required=False, type='str'),
            pn_fabric_retry=dict(required=False, type='int', default=1),
            pn_spine_list=dict(required=False, type='list'),
            pn_leaf_list=dict(required=False, type='list'),
            pn_vrrp_id=dict(required=False, type='str', default='18'),
            pn_csv_data=dict(required=True, type='str'),
        )
    )

    message = ' '
    vrrp_id = module.params['pn_vrrp_id']
    csv_data = module.params['pn_csv_data']
    message += configure_vrrp_l2(module, csv_data, vrrp_id)
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

