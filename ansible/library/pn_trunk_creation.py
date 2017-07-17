#!/usr/bin/python
""" PN Trunk Creation """

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
module: pn_trunk_creation
author: 'Pluribus Networks (devops@pluribusnetworks.com)'
description: Module to create trunks.
Trunk csv file format: switch_name, trunk_name, list of ports.
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
    pn_trunk_data:
      description:
        - String containing trunk data parsed from csv file.
      required: False
      type: str
      default: ''
"""

EXAMPLES = """
- name: Create trunks
  pn_trunk_creation:
    pn_cliusername: "{{ USERNAME }}"
    pn_clipassword: "{{ PASSWORD }}"
    pn_switch_list: "{{ groups['switch'] }}"
    pn_trunk_data: "{{ lookup('file', '{{ trunk_file }}') }}"
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
            task='Create trunks',
            msg='Trunk creation failed',
            changed=False
        )
    else:
        return None


def create_trunk(module, switch, name, ports):
    """
    Method to create a trunk on a switch.
    :param module: The Ansible module to fetch input parameters.
    :param switch: Name of the switch on which to create a trunk
    :param name: The name of the trunk to create.
    :param ports: List of connected ports.
    :return: String describing if trunk got created or not.
    """
    output = ''
    new_trunk = False

    cli = pn_cli(module)
    cli += ' switch %s trunk-show format name no-show-headers ' % switch
    trunk_list = run_cli(module, cli)
    if trunk_list is not None:
        trunk_list = trunk_list.split()
        if name not in trunk_list:
            new_trunk = True

    if new_trunk or trunk_list is None:
        cli = pn_cli(module)
        cli += ' switch %s trunk-create name %s ports %s ' % (switch, name,
                                                              ports)
        run_cli(module, cli)
        CHANGED_FLAG.append(True)
        output += '%s: Created trunk %s\n' % (switch, name)

    return output


def main():
    """ This section is for arguments parsing """
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=False, type='str'),
            pn_clipassword=dict(required=False, type='str', no_log=True),
            pn_switch_list=dict(required=False, type='list', default=[]),
            pn_trunk_data=dict(required=False, type='str', default=''),
        )
    )

    global CHANGED_FLAG
    results = []
    message = ''
    switch_list = module.params['pn_switch_list']

    # Create trunk
    trunk_data = module.params['pn_trunk_data']
    if trunk_data:
        trunk_data = trunk_data.replace(' ', '')
        trunk_data_list = trunk_data.split('\n')
        for row in trunk_data_list:
            if row.startswith('#'):
                continue
            else:
                elements = row.split(',')
                switch_name = elements.pop(0)
                trunk_name = elements.pop(0)
                ports = ','.join(elements)

                if switch_name in switch_list:
                    message += create_trunk(module, switch_name, trunk_name,
                                            ports)

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
        msg='Trunk creation succeeded',
        summary=results,
        exception='',
        failed=False,
        changed=True if True in CHANGED_FLAG else False,
        task='Create trunks'
    )

if __name__ == '__main__':
    main()
