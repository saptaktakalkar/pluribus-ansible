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
short_description: CLI command to create/delete a VLAN.
description:
  - Execute vlan-create or vlan-delete command. 
  - VLANs are used to isolate network traffic at Layer 2.The VLAN identifiers
    0 and 4095 are reserved and cannot be used per the IEEE 802.1Q standard.
    The range of configurable VLAN identifiers is 2 through 4092.
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
      - The C(pn_command) takes the vlan-create/delete command as value.
    required: true
    choices: ['vlan-create', 'vlan-delete']
    type: str
  pn_vlanid:
    description:
      - Specify a VLAN identifier for the VLAN. This is a value between
        2 and 4092.
    required: true
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
    choices: ['stats', 'no-stats']
    type: str
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
  pn_quiet:
    description:
      - Enable/disable system information.
    required: false
    type: bool
    default: true
"""

EXAMPLES = """
- name: create a VLAN
  pn_vlan:
    pn_cliusername: admin
    pn_clipassword: admin
    pn_command: 'vlan-create'
    pn_vlanid: 1854
    pn_scope: fabric

- name: delete VLANs
  pn_vlan:
    pn_cliusername: admin
    pn_clipassword: admin
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


def main():
    """ This section is for arguments parsing """
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=True, type='str'),
            pn_clipassword=dict(required=True, type='str'),
            pn_cliswitch=dict(required=False, type='str'),
            pn_command=dict(required=True, type='str',
                            choices=['vlan-create', 'vlan-delete']),
            pn_vlanid=dict(required=True, type='int'),
            pn_scope=dict(type='str', choices=['fabric', 'local']),
            pn_description=dict(type='str'),
            pn_stats=dict(type='str', choices=['stats', 'no-stats']),
            pn_ports=dict(type='str'),
            pn_untagged_ports=dict(type='str'),
            pn_quiet=dict(default=True, type='bool')
        ),
        required_if=(
            ["pn_command", "vlan-create", ["pn_vlanid", "pn_scope"]],
            ["pn_command", "vlan-delete", ["pn_vlanid"]]
        )
    )

    # Accessing the arguments
    cliusername = module.params['pn_cliusername']
    clipassword = module.params['pn_clipassword']
    cliswitch = module.params['pn_cliswitch']
    command = module.params['pn_command']
    vlanid = module.params['pn_vlanid']
    scope = module.params['pn_scope']
    description = module.params['pn_description']
    stats = module.params['pn_stats']
    ports = module.params['pn_ports']
    untagged_ports = module.params['pn_untagged_ports']
    quiet = module.params['pn_quiet']

    # Building the CLI command string
    cli = '/usr/bin/cli'

    if quiet is True:
        cli += ' --quiet '

    cli += ' --user %s:%s ' % (cliusername, clipassword)

    if cliswitch:
        cli += ' switch-local ' if cliswitch == 'local' else ' switch ' + cliswitch

    if not 2 <= vlanid <= 4092:
        module.exit_json(msg="vLAN id must be between 2 and 4092", changed=False)

    cli += ' ' + command + ' id ' + str(vlanid)

    if scope:
        cli += ' scope ' + scope

    if description:
        cli += ' description ' + description

    if stats:
        cli += ' stats ' + stats

    if ports:
        cli += ' ports ' + ports

    if untagged_ports:
        cli += ' untagged-ports ' + untagged_ports

    # Run the CLI command
    vlancmd = shlex.split(cli)
    response = subprocess.Popen(vlancmd, stderr=subprocess.PIPE,
                                stdout=subprocess.PIPE, universal_newlines=True)

    # 'out' contains the output
    # 'err' contains the error messages
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

# AnsibleModule boilerplate
from ansible.module_utils.basic import AnsibleModule

if __name__ == '__main__':
    main()
