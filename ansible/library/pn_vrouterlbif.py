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
  - Execute vrouter-loopback-interface-add, vrouter-loopback-interface-remove commands.
  - Each fabric, cluster, standalone switch, or virtual network (VNET) can
    provide its tenants with a virtual router (vRouter) service that forwards
    traffic between networks and implements Layer 3 protocols.
options:
  pn_cliusername:
    description:
      - Login username.
    required: true
    type: str
  pn_clipassword:
    description:
      - Login password.
    required: true
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
    required: true
    choices: ['vrouter-loopback-interface-add', 'vrouter-loopback-interface-remove']
    type: str
  pn_vrouter_name:
    description:
      - Specify the name of the vRouter.
    required: true
    type: str
  pn_index:
    description:
      - Specify the interface index fro 1 to 255.
    required: True
    type: int
  pn_interface_ip:
    description:
      - Specify the IP address.
      - Required for vrouter-loopback-interface-add.
    type: str
  pn_quiet:
    description:
      - Enable/disable system information.
    required: false
    type: bool
    default: true
"""

EXAMPLES = """
- name: add vrouter-loopback-interface
  pn_vrouterlbif:
    pn_cliusername: admin pn_clipassword: admin
    pn_command: 'vrouter-loopback-interface-add'
    pn_vrouter_name: 'self'
    pn_index: 10
    pn_interface_ip: 104.104.104.1

- name: remove vrouter-loopback-interface
  pn_vrouterlbif:
    pn_cliusername: admin
    pn_clipassword: admin
    pn_command: 'vrouter-loopback-interface-remove'
    pn_vrouter_name: 'self'
    pn_index: 10
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


def main():
    """ This portion is for arguments parsing """
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=True, type='str'),
            pn_clipassword=dict(required=True, type='str'),
            pn_cliswitch=dict(required=False, type='str'),
            pn_command=dict(required=True, type='str',
                            choices=['vrouter-loopback-interface-add',
                                     'vrouter-loopback-interface-remove']),
            pn_vrouter_name=dict(required=True, type='str'),
            pn_index=dict(type='int'),
            pn_interface_ip=dict(type='str'),
            pn_quiet=dict(default=True, type='bool')
        ),
        required_if=(
            ["pn_command", "vrouter-loopback-interface-add",
             ["pn_vrouter_name", "pn_interface_ip"]],
            ["pn_command", "vrouter-loopback-interface-remove",
             ["pn_vrouter_name", "pn_index"]]
        )
    )

    cliusername = module.params['pn_cliusername']
    clipassword = module.params['pn_clipassword']
    cliswitch = module.params['pn_cliswitch']
    command = module.params['pn_command']
    vrouter_name = module.params['pn_vrouter_name']
    index = module.params['pn_index']
    interface_ip = module.params['pn_interface_ip']
    quiet = module.params['pn_quiet']

    # Building the CLI command string
    cli = '/usr/bin/cli'

    if quiet is True:
        cli += ' --quiet '

    cli += ' --user %s:%s ' % (cliusername, clipassword)

    if cliswitch:
        cli += ' switch-local ' if cliswitch == 'local' else ' switch ' + cliswitch

    cli += ' %s vrouter-name %s ' % (command, vrouter_name)

    if index:
        if not 1 <= index <= 255:
            module.exit_json(msg='Index should be in the range 1 to 255', changed=False)
        cli += ' index ' + str(index)

    if interface_ip:
        cli += ' ip ' + interface_ip

    # Run the CLI command
    vrouterlbcmd = shlex.split(cli)
    response = subprocess.Popen(vrouterlbcmd, stderr=subprocess.PIPE,
                                stdout=subprocess.PIPE, universal_newlines=True)

    # 'out' contains the output
    # 'err' contains the err messages
    out, err = response.communicate()

    # Response in JSON format
    if err:
        module.exit_json(
            command=cli,
            stderr=err.rstrip("\r\n"),
            changed=False
        )

    else:
        module.exit_json(
            command=cli,
            stdout=out.rstrip("\r\n"),
            changed=True
        )

# Ansible boiler-plate
from ansible.module_utils.basic import AnsibleModule

if __name__ == '__main__':
    main()

