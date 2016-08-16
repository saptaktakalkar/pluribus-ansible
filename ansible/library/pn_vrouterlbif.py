#!/usr/bin/python
""" PN CLI vrouter-loopback-interface-add/remove """

# Copyright 2016 Pluribus Networks
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import subprocess
import shlex

DOCUMENTATION = """
---
module: pn_vrouterlbif
author: "Pluribus Networks"
version: 1.0
short_description: CLI command to add/remove vrouter-loopback-interface.
description:
  - Execute vrouter-loopback-interface-add, vrouter-loopback-interface-remove
    commands.
  - Each fabric, cluster, standalone switch, or virtual network (VNET) can
    provide its tenants with a virtual router (vRouter) service that forwards
    traffic between networks and implements Layer 3 protocols.
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
      - Target switch(es) to run the cli on.
    required: False
    type: str
  pn_command:
    description:
      - The C(pn_command) takes the vrouter-loopback-interface command
        as value.
    required: True
    choices: ['vrouter-loopback-interface-add', 'vrouter-loopback-interface-remove']
    type: str
  pn_vrouter_name:
    description:
      - Specify the name of the vRouter.
    required: True
    type: str
  pn_index:
    description:
      - Specify the interface index from 1 to 255.
    type: int
  pn_interface_ip:
    description:
      - Specify the IP address.
    required: True
    type: str
"""

EXAMPLES = """
- name: add vrouter-loopback-interface
  pn_vrouterlbif:
    pn_command: 'vrouter-loopback-interface-add'
    pn_vrouter_name: 'ansible-vrouter'
    pn_interface_ip: '104.104.104.1'

- name: remove vrouter-loopback-interface
  pn_vrouterlbif:
    pn_command: 'vrouter-loopback-interface-remove'
    pn_vrouter_name: 'ansible-vrouter'
    pn_interface_ip: '104.104.104.1'
"""

RETURN = """
command:
  description: the CLI command run on the target node(s).
stdout:
  description: the set of responses from the vrouterlb command.
  returned: always
  type: list
stderr:
  description: the set of error responses from the vrouterlb command.
  returned: on error
  type: list
changed:
  description: Indicates whether the CLI caused changes on the target.
  returned: always
  type: bool
"""


VROUTER_EXISTS = None
LB_INTERFACE_EXISTS = None
# Index range
MIN_INDEX = 1
MAX_INDEX = 255


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
    This method also checks for idempotency using the
    vrouter-loopback-interface-show command.
    If the given vRouter exists, return VROUTER_EXISTS as True else False.
    If a loopback interface with the given ip exists on the given vRouter,
    return LB_INTERFACE_EXISTS as True else False.

    :param module: The Ansible module to fetch input parameters
    :param cli: The CLI string
    :return Global Booleans: VROUTER_EXISTS, LB_INTERFACE_EXISTS
    """
    vrouter_name = module.params['pn_vrouter_name']
    interface_ip = module.params['pn_interface_ip']

    # Global flags
    global VROUTER_EXISTS, LB_INTERFACE_EXISTS

    # Check for vRouter
    check_vrouter = cli + ' vrouter-show format name no-show-headers '
    check_vrouter = shlex.split(check_vrouter)
    out = module.run_command(check_vrouter)[1]
    out = out.split()

    VROUTER_EXISTS = True if vrouter_name in out else False

    # Check for BGP neighbors
    show = cli + ' vrouter-bgp-show vrouter-name %s ' % vrouter_name
    show += 'format neighbor no-show-headers'
    show = shlex.split(show)
    out = module.run_command(show)[1]
    out = out.split()

    LB_INTERFACE_EXISTS = True if interface_ip in out else False


def run_cli(module, cli):
    """
    This method executes the cli command on the target node(s) and returns the
    output. The module then exits based on the output.
    :param cli: the complete cli string to be executed on the target node(s).
    :param module: The Ansible module to fetch command
    """
    command = module.params['pn_command']
    cmd = shlex.split(cli)
    response = subprocess.Popen(cmd, stderr=subprocess.PIPE,
                                stdout=subprocess.PIPE, universal_newlines=True)
    # 'out' contains the output
    # 'err' contains the error messages
    out, err = response.communicate()

    # Response in JSON format
    if err:
        module.exit_json(
            command=cli,
            stderr=err.strip(),
            msg="%s operation failed" % command,
            changed=False
        )

    if out:
        module.exit_json(
            command=cli,
            stdout=out.strip(),
            msg="%s operation completed" % command,
            changed=True
        )

    else:
        module.exit_json(
            command=cli,
            msg="%s operation completed" % command,
            changed=True
        )


def main():
    """ This portion is for arguments parsing """
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=False, type='str'),
            pn_clipassword=dict(required=False, type='str'),
            pn_cliswitch=dict(required=False, type='str'),
            pn_command=dict(required=True, type='str',
                            choices=['vrouter-loopback-interface-add',
                                     'vrouter-loopback-interface-remove']),
            pn_vrouter_name=dict(required=True, type='str'),
            pn_interface_ip=dict(type='str'),
            pn_index=dict(type='int')
        ),
        required_if=(
            ["pn_command", "vrouter-loopback-interface-add",
             ["pn_vrouter_name", "pn_interface_ip"]],
            ["pn_command", "vrouter-loopback-interface-remove",
             ["pn_vrouter_name", "pn_interface_ip"]]
        )
    )

    # Accessing the arguments
    command = module.params['pn_command']
    vrouter_name = module.params['pn_vrouter_name']
    interface_ip = module.params['pn_interface_ip']
    index = module.params['pn_index']

    # Building the CLI command string
    cli = pn_cli(module)

    if index:
        if not MIN_INDEX <= index <= MAX_INDEX:
            module.exit_json(
                msg="Index must be between 1 and 255",
                changed=False
            )
        index = str(index)

    if command == 'vrouter-loopback-interface-remove':
        check_cli(module, cli)
        if LB_INTERFACE_EXISTS is False:
            module.exit_json(
                skipped=True,
                msg=('Loopback interface with IP %s does not exist on %s'
                     % (interface_ip, vrouter_name))
            )
        if not index:
            # To remove loopback interface, we need the index.
            # If index is not specified, get the Loopback interface index
            # using the given interface ip.
            get_index = cli
            get_index += (' vrouter-loopback-interface-show vrouter-name %s ip '
                          '%s ' % (vrouter_name, interface_ip))
            get_index += 'format index no-show-headers'

            get_index = shlex.split(get_index)
            out = module.run_command(get_index)[1]
            index = out.split()[1]

        cli += ' %s vrouter-name %s index %s' % (command, vrouter_name, index)

    if command == 'vrouter-loopback-interface-add':
        check_cli(module, cli)
        if VROUTER_EXISTS is False:
            module.exit_json(
                skipped=True,
                msg=('vRouter %s does not exist. Please create a vRouter first'
                     % vrouter_name)
            )
        if LB_INTERFACE_EXISTS is True:
            module.exit_json(
                skipped=True,
                msg=('Loopback interface with IP %s already exists on %s'
                     % (interface_ip, vrouter_name))
            )
        cli += (' %s vrouter-name %s ip %s'
                % (command, vrouter_name, interface_ip))
        if index:
            cli += ' index %s ' % index

    run_cli(module, cli)

# Ansible boiler-plate
from ansible.module_utils.basic import AnsibleModule

if __name__ == '__main__':
    main()
