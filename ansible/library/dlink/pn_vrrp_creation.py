#!/usr/bin/python
""" PN VRRP Creation """

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
module: pn_vrrp_creation
author: 'Pluribus Networks (devops@pluribusnetworks.com)'
description: Module to configure VRRP on two cluster switches
Vrrp csv file format: vlan id,gateway ip,primary ip,secondary ip,active_switch.
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
    pn_switch_list:
      description:
        - Specify list of all switches.
      required: False
      type: list
      default: []
    pn_vrrp_id:
      description:
        - Specify the vrrp id to be assigned.
      required: False
      default: '18'
      type: str
    pn_vrrp_data:
      description:
        - String containing vlan data parsed from csv file.
      required: False
      type: str
      default: ''
"""

EXAMPLES = """
- name: Configure VRRP on cluster switch
  pn_vrrp_creation:
    pn_cliusername: "{{ USERNAME }}"
    pn_clipassword: "{{ PASSWORD }}"
    pn_switch_list: "{{ groups['switch'] }}"
    pn_vrrp_data: "{{ lookup('file', '{{ vrrp_file }}') }}"
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
    Generate the cli portion to launch the Netvisor cli.
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
    Execute the cli command on the target node(s) and returns the output.
    :param module: The Ansible module to fetch input parameters.
    :param cli: The complete cli string to be executed on the target node(s).
    :return: Output or Error msg depending upon the response from cli else None.
    """
    results = []
    cli = shlex.split(cli)
    rc, out, err = module.run_command(cli)

    if out:
        return out
    if err:
        json_msg = {
            'switch': module.params['pn_switch_list'][0],
            'output': u'Operation Failed: {}'.format(' '.join(cli))
        }
        results.append(json_msg)
        module.exit_json(
            unreachable=False,
            failed=True,
            exception=err.strip(),
            summary=results,
            task='Configure vrrp',
            msg='Vrrp configuration failed',
            changed=False
        )
    else:
        return None


def create_vlan(module, switch, vlan_id, untagged_ports=None):
    """
    Method to create a vlan.
    :param module: The Ansible module to fetch input parameters.
    :param switch: Name of the switch.
    :param vlan_id: vlan id to be created.
    :param untagged_ports: List of untagged ports.
    :return: String describing if vlan got created or not.
    """
    global CHANGED_FLAG
    output = ''
    new_vlan = False

    cli = pn_cli(module)
    cli += ' vlan-show format id no-show-headers '
    existing_vlans = run_cli(module, cli)

    if existing_vlans is not None:
        existing_vlans = existing_vlans.split()
        if vlan_id not in existing_vlans:
            new_vlan = True

    if new_vlan or existing_vlans is None:
        cli = pn_cli(module)
        cli += ' vlan-create id %s scope fabric ' % vlan_id

        if untagged_ports is not None:
            cli += ' untagged-ports %s ' % untagged_ports

        run_cli(module, cli)
        CHANGED_FLAG.append(True)
        output += '%s: Created vlan with id %s\n' % (switch, vlan_id)

    return output


def create_vrouter_interface(module, switch, vrrp_ip, gateway_ip, vlan_id,
                             vrrp_priority):
    """
    Add vrouter interface and assign IP along with vrrp_id and vrrp_priority.
    :param module: The Ansible module to fetch input parameters.
    :param switch: Name of the switch on which to add vrouter interface.
    :param vrrp_ip: Vrrp interface address to be assigned to vrouter interface.
    :param gateway_ip: Gateway interface to be assigned to vrouter.
    :param vlan_id: vlan_id to be assigned.
    :param vrrp_priority: Priority to be given(110 for active switch).
    :return: String describing if vrouter interfaces got added or not.
    """
    global CHANGED_FLAG
    output = ''
    new_gateway, new_vrrp_ip = False, False
    vrrp_id = module.params['pn_vrrp_id']

    # Find vrouter name
    cli = pn_cli(module)
    cli += ' vrouter-show location %s ' % switch
    cli += ' format name no-show-headers '
    vrouter_name = run_cli(module, cli).split()[0]

    cli = pn_cli(module)
    clicopy = cli
    cli += ' vrouter-interface-show vlan %s ip %s ' % (vlan_id, vrrp_ip)
    cli += ' format switch no-show-headers '
    existing_vrouter = run_cli(module, cli)

    if existing_vrouter is not None:
        existing_vrouter = existing_vrouter.split()
        if vrouter_name not in existing_vrouter:
            new_vrrp_ip = True

    if new_vrrp_ip or existing_vrouter is None:
        cli = pn_cli(module)
        cli += ' switch %s ' % switch
        cli += ' vrouter-interface-add vrouter-name %s ' % vrouter_name
        cli += ' ip %s vlan %s if data ' % (vrrp_ip, vlan_id)
        run_cli(module, cli)
        CHANGED_FLAG.append(True)
        output += '%s: Added vrouter interface with ip %s on %s\n' % (
            switch, vrrp_ip, vrouter_name)

    cli = clicopy
    cli += ' vrouter-interface-show vrouter-name %s ' % vrouter_name
    cli += ' ip %s vlan %s ' % (vrrp_ip, vlan_id)
    cli += ' format nic no-show-headers '
    eth_port = run_cli(module, cli).split()
    eth_port.remove(vrouter_name)

    cli = clicopy
    cli += ' vrouter-interface-show vlan %s ' % vlan_id
    cli += ' ip %s vrrp-primary %s ' % (gateway_ip, eth_port[0])
    cli += ' format switch no-show-headers '
    existing_vrouter = run_cli(module, cli)
    if existing_vrouter is not None:
        existing_vrouter = existing_vrouter.split()
        if vrouter_name not in existing_vrouter:
            new_gateway = True

    if new_gateway or existing_vrouter is None:
        cli = clicopy
        cli += ' switch %s ' % switch
        cli += ' vrouter-interface-add vrouter-name %s ' % vrouter_name
        cli += ' ip %s vlan %s if data vrrp-id %s ' % (gateway_ip, vlan_id,
                                                       vrrp_id)
        cli += ' vrrp-primary %s vrrp-priority %s ' % (eth_port[0],
                                                       vrrp_priority)
        run_cli(module, cli)
        CHANGED_FLAG.append(True)
        output += '%s: Added vrouter interface with ip %s on %s\n' % (
            switch, gateway_ip, vrouter_name)

    return output


def main():
    """ This section is for arguments parsing """
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=False, type='str'),
            pn_clipassword=dict(required=False, type='str', no_log=True),
            pn_switch_list=dict(required=False, type='list', default=[]),
            pn_vrrp_id=dict(required=False, type='str', default='18'),
            pn_vrrp_data=dict(required=False, type='str', default=''),
        )
    )

    global CHANGED_FLAG
    results = []
    message = ''
    switch_list = module.params['pn_switch_list']

    # Configure vrrp
    vrrp_data = module.params['pn_vrrp_data']
    if vrrp_data:
        vrrp_data = vrrp_data.replace(' ', '')
        vrrp_data_list = vrrp_data.split('\n')
        for row in vrrp_data_list:
            if row.startswith('#'):
                continue
            else:
                elements = row.split(',')
                vlan_id = elements.pop(0).strip()
                gateway_ip = elements.pop(0).strip()
                primary_ip = elements.pop(0).strip()
                secondary_ip = elements.pop(0).strip()
                active_switch = elements.pop(0).strip()

                message += create_vlan(module, switch_list[0], vlan_id)

                for switch in switch_list:
                    if switch == active_switch:
                        vrrp_priority = '110'
                        vrrp_ip = primary_ip
                    else:
                        vrrp_priority = '109'
                        vrrp_ip = secondary_ip

                    message += create_vrouter_interface(module, switch, vrrp_ip,
                                                        gateway_ip, vlan_id,
                                                        vrrp_priority)

    for switch in switch_list:
        replace_string = switch + ': '
        for line in message.splitlines():
            if replace_string in line:
                results.append({
                    'switch': switch,
                    'output': (line.replace(replace_string, '')).strip()
                })

    # Exit the module and return the required JSON.
    module.exit_json(
        unreachable=False,
        msg='Vrrp configuration succeeded',
        summary=results,
        exception='',
        failed=False,
        changed=True if True in CHANGED_FLAG else False,
        task='Configure vrrp'
    )

if __name__ == '__main__':
    main()

