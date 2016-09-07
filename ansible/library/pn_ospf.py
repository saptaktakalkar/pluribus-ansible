#!/usr/bin/python
""" PN-CLI vrouter-ospf-add/remove """

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

import subprocess
import shlex

DOCUMENTATION = """
---
module: pn_ospf
author: "Pluribus Networks"
version: 1.0
short_description: CLI command to add/remove ospf protocol to a vRouter.
description:
  - Execute vrouter-ospf-add, vrouter-ospf-remove command.
  - This command adds/removes Open Shortest Path First(OSPF) routing
    protocol to a virtual router(vRouter) service.
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
      - Target switch to run the CLI on.
    required: False
    type: str
  pn_command:
    description:
      - The C(pn_command) takes the vrouter-ospf add/remove
        command as value.
    required: True
    choices: ['vrouter-ospf-add', 'vrouter-ospf-remove']
    type: str
  pn_vrouter_name:
    description:
      - specify the name of the vRouter.
    required: True
    type: str
  pn_network_ip:
    description:
      - Specify the network IP address.
    required: True
    type: str
  pn_ospf_area:
    description:
    - Stub area number for the configuration. Required for vrouter-ospf-add.
    type: str
"""

EXAMPLES = """
- name: "Add OSPF to vrouter"
  pn_ospf:
    pn_command: vrouter-ospf-add
    pn_vrouter_name: name-string
    pn_network_ip: 192.168.11.2/24
    pn_ospf_area: 1.0.0.0

- name: "Remove OSPF from vrouter"
  pn_ospf:
    pn_command: vrouter-ospf-remove
    pn_vrouter_name: name-string
"""

RETURN = """
command:
  description: the CLI command run on the target node(s).
stdout:
  description: the set of responses from the ospf command.
  returned: always
  type: list
stderr:
  description: the set of error responses from the ospf command.
  returned: on error
  type: list
changed:
  description: Indicates whether the CLI caused changes on the target.
  returned: always
  type: bool
"""


VROUTER_EXISTS = None
NETWORK_EXISTS = None


def pn_cli(module):
    """
    This method is to generate the cli portion to launch the Netvisor cli.
    It parses the username, password, switch parameters from module.
    :param module: The Ansible module to fetch username, password and switch
    :return: returns the cli string for further processing
    """
    username = module.params['pn_cliusername']
    password = module.params['pn_clipassword']
    cliswitch = module.params['pn_cliswitch']

    if username and password:
        cli = '/usr/bin/cli --quiet --user %s:%s ' % (username, password)
    else:
        cli = '/usr/bin/cli --quiet '

    cli += ' switch-local ' if cliswitch == 'local' else ' switch ' + cliswitch
    return cli


def check_cli(module, cli):
    """
    This method checks if vRouter exists on the target node.
    This method also checks for idempotency using the vrouter-ospf-show command.
    If the given vRouter exists, return VROUTER_EXISTS as True else False.
    If an OSPF network with the given ip exists on the given vRouter,
    return NETWORK_EXISTS as True else False.

    :param module: The Ansible module to fetch input parameters
    :param cli: The CLI string
    :return Global Booleans: VROUTER_EXISTS, NETWORK_EXISTS
    """
    vrouter_name = module.params['pn_vrouter_name']
    network_ip = module.params['pn_network_ip']
    # Global flags
    global VROUTER_EXISTS, NETWORK_EXISTS

    # Check for vRouter
    check_vrouter = cli + ' vrouter-show format name no-show-headers '
    check_vrouter = shlex.split(check_vrouter)
    out = module.run_command(check_vrouter)[1]
    out = out.split()

    VROUTER_EXISTS = True if vrouter_name in out else False

    # Check for OSPF networks
    show = cli + ' vrouter-ospf-show vrouter-name %s ' % vrouter_name
    show += 'format network no-show-headers'
    show = shlex.split(show)
    out = module.run_command(show)[1]
    out = out.split()

    NETWORK_EXISTS = True if network_ip in out else False


def run_cli(module, cli):
    """
    This method executes the cli command on the target node(s) and returns the
    output. The module then exits based on the output.
    :param cli: the complete cli string to be executed on the target node(s).
    :param module: The Ansible module to fetch command
    """
    cliswitch = module.params['pn_cliswitch']
    command = module.params['pn_command']
    cmd = shlex.split(cli)
    response = subprocess.Popen(cmd, stderr=subprocess.PIPE,
                                stdout=subprocess.PIPE, universal_newlines=True)
    # 'out' contains the output
    # 'err' contains the error messages
    out, err = response.communicate()

    print_cli = cli.split(cliswitch)[1]

    # Response in JSON format
    if err:
        module.exit_json(
            command=print_cli,
            stderr=err.strip(),
            msg="%s operation failed" % command,
            changed=False
        )

    if out:
        module.exit_json(
            command=print_cli,
            stdout=out.strip(),
            msg="%s operation completed" % command,
            changed=True
        )

    else:
        module.exit_json(
            command=print_cli,
            msg="%s operation completed" % command,
            changed=True
        )


def main():
    """ This section is for arguments parsing """
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=False, type='str'),
            pn_clipassword=dict(required=False, type='str'),
            pn_cliswitch=dict(required=False, type='str', default='local'),
            pn_command=dict(required=True, type='str',
                            choices=['vrouter-ospf-add',
                                     'vrouter-ospf-remove']),
            pn_vrouter_name=dict(required=True, type='str'),
            pn_network_ip=dict(required=True, type='str'),
            pn_ospf_area=dict(type='str')
        ),
        required_if=(
            ['pn_command', 'vrouter-ospf-add',
             ['pn_network_ip', 'pn_ospf_area']],
            ['pn_command', 'vrouter-ospf-remove', ['pn_network_ip']]
        )
    )

    # Accessing the arguments
    command = module.params['pn_command']
    vrouter_name = module.params['pn_vrouter_name']
    network_ip = module.params['pn_network_ip']
    ospf_area = module.params['pn_ospf_area']

    # Building the CLI command string
    cli = pn_cli(module)
    check_cli(module, cli)

    if command == 'vrouter-ospf-add':
        if VROUTER_EXISTS is False:
            module.exit_json(
                skipped=True,
                msg='vRouter %s does not exist' % vrouter_name
            )
        if NETWORK_EXISTS is True:
            module.exit_json(
                skipped=True,
                msg=('OSPF with network ip %s already exists on %s'
                     % (network_ip, vrouter_name))
            )
        cli += (' %s vrouter-name %s network %s ospf-area %s'
                % (command, vrouter_name, network_ip, ospf_area))

    if command == 'vrouter-ospf-remove':
        if VROUTER_EXISTS is False:
            module.exit_json(
                skipped=True,
                msg='vRouter %s does not exist' % vrouter_name
            )
        if NETWORK_EXISTS is False:
            module.exit_json(
                skipped=True,
                msg=('OSPF with network ip %s already exists on %s'
                     % (network_ip, vrouter_name))
            )
        cli += (' %s vrouter-name %s network %s'
                % (command, vrouter_name, network_ip))

    run_cli(module, cli)
# AnsibleModule boilerplate
from ansible.module_utils.basic import AnsibleModule

if __name__ == '__main__':
    main()

