#!/usr/bin/python
""" PN Vlag Creation """

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
module: pn_vlag_creation
author: 'Pluribus Networks (devops@pluribusnetworks.com)'
description: Module to create vlags.
Vlag csv format: vlag_name, local_switch, local_port, peer_switch, peer_port.
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
    pn_vlag_data:
      description:
        - String containing vlag data parsed from csv file.
      required: False
      type: str
      default: ''
"""

EXAMPLES = """
- name: Create vlags
  pn_vlag_creation:
    pn_cliusername: "{{ USERNAME }}"
    pn_clipassword: "{{ PASSWORD }}"
    pn_switch_list: "{{ groups['switch'] }}"
    pn_vlag_data: "{{ lookup('file', '{{ vlag_file }}') }}"
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
            task='Create vlags',
            msg='vlag creation failed',
            changed=False
        )
    else:
        return None


def create_vlag(module, name, switch, port, peer_switch, peer_port):
    """
    Create virtual link aggregation groups.
    :param module: The Ansible module to fetch input parameters.
    :param name: The name of the vlag to create.
    :param switch: Name of the local switch.
    :param port: Name of the trunk on local switch.
    :param peer_switch: Name of the peer switch.
    :param peer_port: Name of the trunk on peer switch.
    :return: String describing if vlag got created or not.
    """
    output = ''
    new_vlag = False

    cli = pn_cli(module)
    cli += ' switch %s vlag-show format switch,peer-switch, ' % switch
    cli += ' no-show-headers '
    vlag_list = run_cli(module, cli)
    if vlag_list is not None:
        vlag_list = vlag_list.split()
        if peer_switch not in vlag_list:
            new_vlag = True

    if new_vlag or vlag_list is None:
        cli = pn_cli(module)
        cli += ' switch %s vlag-create name %s port %s ' % (switch, name, port)
        cli += ' peer-switch %s peer-port %s ' % (peer_switch, peer_port)
        cli += ' mode active-active '
        run_cli(module, cli)
        CHANGED_FLAG.append(True)
        output += '%s: Configured vLag %s\n' % (switch, name)

    return output


def main():
    """ This section is for arguments parsing """
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=False, type='str'),
            pn_clipassword=dict(required=False, type='str', no_log=True),
            pn_switch_list=dict(required=False, type='list', default=[]),
            pn_vlag_data=dict(required=False, type='str', default=''),
        )
    )

    global CHANGED_FLAG
    results = []
    message = ''

    # Create vlag
    vlag_data = module.params['pn_vlag_data']
    if vlag_data:
        vlag_data = vlag_data.replace(' ', '')
        vlag_data_list = vlag_data.split('\n')
        for row in vlag_data_list:
            if row.startswith('#'):
                continue
            else:
                elements = row.split(',')
                if len(elements) == 5:
                    vlag_name = elements[0].strip()
                    local_switch = elements[1].strip()
                    local_ports = elements[2].strip()
                    peer_switch = elements[3].strip()
                    peer_ports = elements[4].strip()

                    message += create_vlag(module, vlag_name, local_switch,
                                           local_ports, peer_switch, peer_ports)

    for switch in module.params['pn_switch_list']:
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
        msg='vlag creation succeeded',
        summary=results,
        exception='',
        failed=False,
        changed=True if True in CHANGED_FLAG else False,
        task='Create vlags'
    )

if __name__ == '__main__':
    main()
