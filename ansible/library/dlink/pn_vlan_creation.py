#!/usr/bin/python
""" PN Vlan Creation """

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
module: pn_vlan_creation
author: 'Pluribus Networks (devops@pluribusnetworks.com)'
description: Module to create vlans.
Vlan csv file format: vlan id, list of untagged ports.
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
    pn_switch:
      description:
        - Name of the switch on which this task is currently getting executed.
      required: True
      type: str
    pn_vlan_data:
      description:
        - String containing vlan data parsed from csv file.
      required: False
      type: str
      default: ''
"""

EXAMPLES = """
- name: Create vlans
  pn_vlan_creation:
    pn_cliusername: "{{ USERNAME }}"
    pn_clipassword: "{{ PASSWORD }}"
    pn_switch: "{{ inventory_hostname }}"
    pn_vlan_data: "{{ lookup('file', '{{ vlan_file }}') }}"
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
            'switch': module.params['pn_switch'],
            'output': u'Operation Failed: {}'.format(' '.join(cli))
        }
        results.append(json_msg)
        module.exit_json(
            unreachable=False,
            failed=True,
            exception=err.strip(),
            summary=results,
            task='Create vlans',
            msg='vlan creation failed',
            changed=False
        )
    else:
        return None


def create_vlan(module, vlan_id, untagged_ports):
    """
    Method to create a vlan.
    :param module: The Ansible module to fetch input parameters.
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
        output += 'Created vlan with id %s\n' % vlan_id

    return output


def main():
    """ This section is for arguments parsing """
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=False, type='str'),
            pn_clipassword=dict(required=False, type='str', no_log=True),
            pn_switch=dict(required=True, type='str'),
            pn_vlan_data=dict(required=False, type='str', default=''),
        )
    )

    global CHANGED_FLAG
    results = []
    message = ''

    # Create vlans
    vlan_data = module.params['pn_vlan_data']
    if vlan_data:
        vlan_data = vlan_data.replace(' ', '')
        vlan_data_list = vlan_data.split('\n')
        for row in vlan_data_list:
            if row.startswith('#'):
                continue
            else:
                elements = row.split(',')
                elements = filter(None, elements)
                vlan_id = elements.pop(0).strip()
                if len(elements) > 0:
                    untagged_ports = ','.join(elements)
                else:
                    untagged_ports = None

                message += create_vlan(module, vlan_id, untagged_ports)

    for line in message.splitlines():
        if line:
            results.append({
                'switch': module.params['pn_switch'],
                'output': line
            })

    # Exit the module and return the required JSON.
    module.exit_json(
        unreachable=False,
        msg='vlan creation succeeded',
        summary=results,
        exception='',
        failed=False,
        changed=True if True in CHANGED_FLAG else False,
        task='Create vlans'
    )

if __name__ == '__main__':
    main()

