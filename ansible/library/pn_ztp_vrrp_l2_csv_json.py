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

from ansible.module_utils.basic import AnsibleModule
import shlex
import json

DOCUMENTATION = """
---
module: pn_ztp_vrrp_l2_csv
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
    - name: Configure VRRP L2 setup
      pn_ztp_vrrp_l2_csv:
        pn_cliusername: "{{ USERNAME }}"
        pn_clipassword: "{{ PASSWORD }}"
        pn_spine_list: "{{ groups['spine'] }}"
        pn_leaf_list: "{{ groups['leaf'] }}"
        pn_vrrp_id: '18'
        pn_csv_data: "{{ lookup('file', '{{ csv_file }}') }}"
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


def create_vlan(module, vlan_id, switch):
    """
    Method to create a vlan.
    :param module: The Ansible module to fetch input parameters.
    :param vlan_id: vlan id to be created.
    :param switch: Name of the switch on which vlan creation will be executed.
    :return: String describing if vlan got created or if it already exists.
    """
    global CHANGED_FLAG
    cli = pn_cli(module)
    clicopy = cli

    cli += ' vlan-show format id no-show-headers '
    existing_vlans = run_cli(module, cli).split()
    existing_vlans = list(set(existing_vlans))

    if vlan_id not in existing_vlans:
        cli = clicopy
        cli += ' vlan-create id %s scope fabric ' % vlan_id
        run_cli(module, cli)
        CHANGED_FLAG.append(True)
        return ' %s: Vlan id %s with scope fabric created successfully \n' % (
            switch, vlan_id
        )
    else:
        return ' %s: Vlan id %s with scope fabric already exists \n' % (
            switch, vlan_id
        )


def get_vrouter_name(module, switch_name):
    """
    Method to return name of the vrouter.
    :param module: The Ansible module to fetch input parameters.
    :param switch_name: Name of the switch for which to find the vrouter.
    :return: Vrouter name.
    """
    cli = pn_cli(module)
    cli += ' vrouter-show location ' + switch_name
    cli += ' format name no-show-headers '
    return run_cli(module, cli).split()[0]


def create_vrouter(module, switch, vrrp_id, vnet_name):
    """
    Method to create vrouter and assign vrrp_id to the switches.
    :param module: The Ansible module to fetch input parameters.
    :param switch: The switch name on which vrouter will be created.
    :param vrrp_id: The vrrp_id to be assigned.
    :return: The output string informing details of vrouter created and
    interface added or if vrouter already exists.
    """
    global CHANGED_FLAG
    vrouter_name = switch + '-vrouter'
    cli = pn_cli(module)
    cli += ' switch ' + switch
    clicopy = cli

    # Check if vrouter already exists
    cli += ' vrouter-show format name no-show-headers '
    existing_vrouter_names = run_cli(module, cli).split()

    # If vrouter doesn't exists then create it
    if vrouter_name not in existing_vrouter_names:
        cli = clicopy
        cli += ' vrouter-create name %s vnet %s hw-vrrp-id %s enable ' % (
            vrouter_name, vnet_name, vrrp_id
        )
        run_cli(module, cli)
        CHANGED_FLAG.append(True)
        return ' %s: Created vrouter with name %s \n' % (switch, vrouter_name)
    else:
        return ' %s: Vrouter with name %s already exists \n' % (switch,
                                                                vrouter_name)


def create_vrouter_interface(module, switch, ip, vlan_id, vrrp_id, ip_count,
                             vrrp_priority):
    """
    Method to add vrouter interface and assign IP to it along with
    vrrp_id and vrrp_priority.
    :param module: The Ansible module to fetch input parameters.
    :param switch: The switch name on which interfaces will be created.
    :param ip: IP address to be assigned to vrouter interface.
    :param vlan_id: vlan_id to be assigned.
    :param vrrp_id: vrrp_id to be assigned.
    :param vrrp_priority: priority to be given(110 for active switch).
    :param ip_count: The value of fourth octet in the ip
    :return: String describing if vrouter interface got added or not.
    """
    global CHANGED_FLAG
    vrouter_name = get_vrouter_name(module, switch)
    ip_addr = ip.split('.')
    fourth_octet = ip_addr[3].split('/')
    subnet = fourth_octet[1]

    static_ip = ip_addr[0] + '.' + ip_addr[1] + '.' + ip_addr[2] + '.'
    ip1 = static_ip + '1' + '/' + subnet
    ip2 = static_ip + ip_count + '/' + subnet

    cli = pn_cli(module)
    clicopy = cli
    cli += ' vrouter-interface-show vlan %s ip %s ' % (vlan_id, ip2)
    cli += ' format switch no-show-headers '
    existing_vrouter = run_cli(module, cli).split()
    existing_vrouter = list(set(existing_vrouter))

    if vrouter_name not in existing_vrouter:
        cli = clicopy
        cli += ' vrouter-interface-add vrouter-name ' + vrouter_name
        cli += ' ip ' + ip2
        cli += ' vlan %s if data ' % vlan_id
        run_cli(module, cli)
        output = ' %s: Added vrouter interface with ip %s on %s \n' % (
            switch, ip2, vrouter_name
        )
        CHANGED_FLAG.append(True)
    else:
        output = ' %s: Vrouter interface %s already exists on %s \n' % (
            switch, ip2, vrouter_name
        )

    cli = clicopy
    cli += ' vrouter-interface-show vrouter-name %s ip %s vlan %s ' % (
        vrouter_name, ip2, vlan_id
    )
    cli += ' format nic no-show-headers '
    eth_port = run_cli(module, cli).split()
    eth_port.remove(vrouter_name)

    cli = clicopy
    cli += ' vrouter-interface-show vlan %s ip %s vrrp-primary %s ' % (
        vlan_id, ip1, eth_port[0]
    )
    cli += ' format switch no-show-headers '
    existing_vrouter = run_cli(module, cli).split()
    existing_vrouter = list(set(existing_vrouter))

    if vrouter_name not in existing_vrouter:
        cli = clicopy
        cli += ' vrouter-interface-add vrouter-name ' + vrouter_name
        cli += ' ip ' + ip1
        cli += ' vlan %s if data vrrp-id %s ' % (vlan_id, vrrp_id)
        cli += ' vrrp-primary %s vrrp-priority %s ' % (eth_port[0],
                                                       vrrp_priority)
        run_cli(module, cli)
        output += ' %s: Added vrouter interface with ip %s on %s \n' % (
            switch, ip1, vrouter_name
        )
        CHANGED_FLAG.append(True)

    else:
        output += ' %s: Vrouter interface %s already exists on %s \n' % (
            switch, ip1, vrouter_name
        )

    return output


def configure_vrrp(module, vrrp_id, vrrp_ip, active_switch, vlan_id):
    """
    Method to configure vrrp interfaces.
    :param module: The Ansible module to fetch input parameters.
    :param vrrp_id: The vrrp_id need to be assigned.
    :param vrrp_ip: The vrrp_ip needed to be assigned.
    :param active_switch: The name of the active switch.
    :param vlan_id: The vlan_id to be assigned.
    :return: Output of the created vrrp configuration.
    """
    output = create_vlan(module, vlan_id, active_switch)
    host_count = 1
    for spine in module.params['pn_spine_list']:
        host_count += 1
        vrrp_priority = '110' if spine == active_switch else '109'
        output += create_vrouter_interface(module, spine, vrrp_ip, vlan_id,
                                           vrrp_id, str(host_count),
                                           vrrp_priority)
    return output


def configure_vrrp_l2(module, csv_data, vrrp_id):
    """
    Method to configure VRRP for L2.
    :param module: The Ansible module to fetch input parameters.
    :param csv_data: CSV data describing different vrrp attributes.
    :param vrrp_id: The vrrp id to be assigned.
    :return: Output of created vrrp configuration.
    """
    output = ''
    cli = pn_cli(module)
    cli += ' fabric-node-show format fab-name no-show-headers '
    fabric_name = list(set(run_cli(module, cli).split()))[0]
    vnet_name = str(fabric_name) + '-global'

    for switch in module.params['pn_spine_list']:
        output += create_vrouter(module, switch, vrrp_id, vnet_name)

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
            pn_spine_list=dict(required=False, type='list'),
            pn_leaf_list=dict(required=False, type='list'),
            pn_vrrp_id=dict(required=False, type='str', default='18'),
            pn_csv_data=dict(required=True, type='str'),
        )
    )

    global CHANGED_FLAG
    message = configure_vrrp_l2(module, module.params['pn_csv_data'],
                                module.params['pn_vrrp_id'])

    message_string = message
    results = []
    switch_list = module.params['pn_spine_list'] + module.params['pn_leaf_list']
    for switch in switch_list:
        replace_string = switch + ': '

        for line in message_string.splitlines():
            if replace_string in line:
                #info.append((line.replace(replace_string, '')).strip())
                json_msg = {'switch' : switch , 'output' : (line.replace(replace_string, '')).strip() }
                results.append(json_msg)

    # Exit the module and return the required JSON.
    module.exit_json(
         summary=results,
         stdout='abc',
         error='0',
         failed=False,
         changed=True if True in CHANGED_FLAG else False
    )


if __name__ == '__main__':
    main()

