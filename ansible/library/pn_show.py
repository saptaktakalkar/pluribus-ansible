#!/usr/bin/python
""" PN CLI show commands """

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
module: pn_show
author: "Pluribus Networks"
version: 1.0
short_description: Run show commands on nvOS device.
description:
  - Execute show command in the nodes and returns the results
    read from the device.
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
      - The C(pn_command) takes a CLI show command as value.
    required: true
    type: str
  pn_parameters:
    description:
      - Display output using a specific parameter. Use 'all' to display possible
        output. List of comman separated parameters.
    type: str
  pn_options:
    description:
      - Specify formatting options.
    type: str
"""

EXAMPLES = """
- name: run the vlan-show command
  pn_show:
    pn_command: 'vlan-show'
    pn_parameters: id,scope,ports
    pn_options: 'layout vertical'

- name: run the vlag-show command
  pn_show:
    pn_command: 'vlag-show'
    pn_parameters: 'id,name,cluster,mode'
    pn_options: 'no-show-headers'

- name: run the cluster-show command
  pn_show:
    pn_command: 'cluster-show'
"""

RETURN = """
command:
  description: the CLI command run on the target node(s).
stdout:
  description: the set of responses from the show command.
  returned: always
  type: list
stderr:
  description: the set of error responses from the show command.
  returned: on error
  type: list
changed:
  description: Indicates whether the CLI caused any change on the target.
  returned: always(False)
  type: bool
"""


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
    if cliswitch:
        cli += (' switch-local ' if cliswitch == 'local' else ' switch ' +
                cliswitch)
    return cli


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

    if cli
    print_cli = cli.split(cliswitch)[1]

    # Response in JSON format
    if err:
        module.exit_json(
            command=print_cli,
            msg='%s: ' % command,
            stderr=err.strip(),
            changed=False
        )

    if out:
        module.exit_json(
            command=print_cli,
            msg='%s: ' % command,
            stdout=out.strip(),
            changed=False
        )

    else:
        module.exit_json(
            command=cli,
            msg='%s: Nothing to display!!!' % command,
            changed=False
        )


def main():
    """ This section is for arguments parsing """
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=True, type='str'),
            pn_clipassword=dict(required=True, type='str'),
            pn_cliswitch=dict(required=False, type='str'),
            pn_command=dict(required=True, type='str'),
            pn_parameters=dict(default='all', type='str'),
            pn_options=dict(type='str')
        )
    )

    # Accessing the arguments
    command = module.params['pn_command']
    parameters = module.params['pn_parameters']
    options = module.params['pn_options']

    # Building the CLI command string
    cli = pn_cli(module)

    cli += ' %s format %s ' % (command, parameters)

    if options:
        cli += options

    run_cli(module, cli)

# AnsibleModule boilerplate
from ansible.module_utils.basic import AnsibleModule

if __name__ == '__main__':
    main()

