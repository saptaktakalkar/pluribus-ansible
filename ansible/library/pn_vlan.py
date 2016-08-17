#!/usr/bin/python
""" PN CLI vlan-create/vlan-delete """

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
module: pn_vlan
author: "Pluribus Networks"
version: 1.0
short_description: CLI command to create/delete a VLAN.
description:
  - Execute vlan-create or vlan-delete command.
  - VLANs are used to isolate network traffic at Layer 2.The VLAN identifiers
    0 and 4095 are reserved and cannot be used per the IEEE 802.1Q standard.
    The range of configurable VLAN identifiers is 2 through 4092.
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
      - The C(pn_command) takes the vlan-create/delete command as value.
    required: True
    choices: ['vlan-create', 'vlan-delete']
    type: str
  pn_vlanid:
    description:
      - Specify a VLAN identifier for the VLAN. This is a value between
        2 and 4092.
    required: True
    type: int
  pn_scope:
    description:
      - Specify a scope for the VLAN.
      - Required for vlan-create.
    choices: ['fabric', 'local']
    type: str
  pn_description:
    description:
      - Specify a description for the VLAN.
    type: str
  pn_stats:
    description:
      - Specify if you want to collect statistics for a VLAN. Statistic
        collection is enabled by default.
    type: bool
  pn_ports:
    description:
      - Specifies the switch network data port number, list of ports, or range
        of ports. Port numbers must ne in the range of 1 to 64.
    type: str
  pn_untagged_ports:
    description:
      - Specifies the ports that should have untagged packets mapped to the
        VLAN. Untagged packets are packets that do not contain IEEE 802.1Q VLAN
        tags.
    type: str
"""

EXAMPLES = """
- name: create a VLAN
  pn_vlan:
    pn_command: 'vlan-create'
    pn_vlanid: 1854
    pn_scope: fabric

- name: delete VLANs
  pn_vlan:
    pn_command: 'vlan-delete'
    pn_vlanid: 1854
"""

RETURN = """
command:
  description: the CLI command run on the target node(s).
stdout:
  description: the set of responses from the vlan command.
  returned: always
  type: list
stderr:
  description: the set of error responses from the vlan command.
  returned: on error
  type: list
changed:
  description: Indicates whether the CLI caused changes on the target.
  returned: always
  type: bool
"""

VLAN_EXISTS = None
MAX_VLAN_ID = 4092
MIN_VLAN_ID = 2


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
    This method checks for idempotency using the vlan-show command.
    If a vlan with given vlan id exists, return VLAN_EXISTS as True else False.
    :param module: The Ansible module to fetch input parameters
    :param cli: The CLI string
    :return Global Booleans: VLAN_EXISTS
    """
    vlanid = module.params['pn_vlanid']

    show = cli + ' vlan-show id %s format id,scope no-show-headers' % str(vlanid)
    show = shlex.split(show)
    out = module.run_command(show)[1]

    out = out.split()
    # Global flags
    global VLAN_EXISTS
    VLAN_EXISTS = True if str(vlanid) in out else False


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
                            choices=['vlan-create', 'vlan-delete']),
            pn_vlanid=dict(required=True, type='int'),
            pn_scope=dict(type='str', choices=['fabric', 'local']),
            pn_description=dict(type='str'),
            pn_stats=dict(type='bool'),
            pn_ports=dict(type='str'),
            pn_untagged_ports=dict(type='str')
        ),
        required_if=(
            ["pn_command", "vlan-create", ["pn_vlanid", "pn_scope"]],
            ["pn_command", "vlan-delete", ["pn_vlanid"]]
        )
    )

    # Accessing the arguments
    command = module.params['pn_command']
    vlanid = module.params['pn_vlanid']
    scope = module.params['pn_scope']
    description = module.params['pn_description']
    stats = module.params['pn_stats']
    ports = module.params['pn_ports']
    untagged_ports = module.params['pn_untagged_ports']

    # Building the CLI command string
    cli = pn_cli(module)

    if not MIN_VLAN_ID <= vlanid <= MAX_VLAN_ID:
        module.exit_json(
            msg="VLAN id must be between 2 and 4092",
            changed=False
        )

    if command == 'vlan-create':

        check_cli(module, cli)
        if VLAN_EXISTS is True:
            module.exit_json(
                skipped=True,
                msg='VLAN with id %s already exists' % str(vlanid)
            )

        cli += ' %s id %s scope %s ' % (command, str(vlanid), scope)

        if description:
            cli += ' description ' + description

        if stats is True:
            cli += ' stats '
        if stats is False:
            cli += ' no-stats '

        if ports:
            cli += ' ports ' + ports

        if untagged_ports:
            cli += ' untagged-ports ' + untagged_ports

    if command == 'vlan-delete':

        check_cli(module, cli)
        if VLAN_EXISTS is False:
            module.exit_json(
                skipped=True,
                msg='VLAN with id %s does not exist' % str(vlanid)
            )

        cli += ' %s id %s ' % (command, str(vlanid))

    run_cli(module, cli)

# AnsibleModule boilerplate
from ansible.module_utils.basic import AnsibleModule

if __name__ == '__main__':
    main()

