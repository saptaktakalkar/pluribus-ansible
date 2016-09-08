#!/usr/bin/python
""" PN CLI vlag-create/vlag-delete/vlag-modify """

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
module: pn_vlag
author: "Pluribus Networks"
version: 1.0
short_description: CLI command to create/delete/modify vlag.
description:
  - Execute vlag-create/vlag-delete/vlag-modify command.
  - A virtual link aggregation group (VLAG) allows links that are physically
    connected to two different Pluribus Networks devices to appear as a single
    trunk to a third device. The third device can be a switch, server, or any
    Ethernet device. A VLAG can provide Layer 2 multipathing, which allows you
    to create redundancy by increasing bandwidth, enabling multiple parallel
    paths between nodes and loadbalancing traffic where alternative paths exist.
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
      - Target switch(es) to run this command on.
    type: str
  pn_command:
    description:
      - The C(pn_command) takes the vlag-create/delete/modify command as value.
    required: true
    choices: ['vlag-create', 'vlag-delete', 'vlag-modify']
    type: str
  pn_name:
    description:
      - The C(pn_name) takes a valid name for vlag configuration.
    required: true
    type: str
  pn_port:
    description:
      - Specify the local VLAG port.
      - Required for vlag-create.
    type: str
  pn_peer_port:
    description:
      - Specify the peer VLAG port.
      - Required for vlag-create.
    type: str
  pn_mode:
    description:
      - Specify the mode for the VLAG. Active-standby indicates one side is
        active and the other side is in standby mode. Active-active indicates
        that both sides of the vlag are up by default.
    choices: ['active-active', 'active-standby']
    type: str
  pn_peer_switch:
    description:
      - Specify the fabric-name of the peer switch.
    type: str
  pn_failover_action:
    description:
      - Specify the failover action as move or ignore.
    choices: ['move', 'ignore']
    type: str
  pn_lacp_mode:
    description:
      - Specify the LACP mode.
    choices: ['off', 'passive', 'active']
    type: str
  pn_lacp_timeout:
    description:
      - Specify the LACP timeout as slow(30 seconds) or fast(4 seconds).
    choices: ['slow', 'fast']
    type: str
  pn_lacp_fallback:
    description:
      - Specify the LACP fallback mode as bundles or individual.
    choices: ['bundle', 'individual']
    type: str
  pn_lacp_fallback_timeout:
    description:
      - Specify the LACP fallback timeout in seconds. The range is between 30
        and 60 seconds with a default value of 50 seconds.
    type: str
"""

EXAMPLES = """
- name: create a VLAG
  pn_vlag:
    pn_command: 'vlag-create'
    pn_name: spine-to-leaf
    pn_port: 'spine01-to-leaf'
    pn_peer_port: 'spine02-to-leaf'
    pn_peer_switch: spine02
    pn_mode: 'active-active'

- name: delete VLAGs
  pn_vlag:
    pn_command: 'vlag-delete'
    pn_name: spine-to-leaf
"""

RETURN = """
command:
  description: the CLI command run on the target node(s).
stdout:
  description: the set of responses from the vlag command.
  returned: always
  type: list
stderr:
  description: the set of error responses from the vlag command.
  returned: on error
  type: list
changed:
  description: Indicates whether the CLI caused changes on the target.
  returned: always
  type: bool
"""

VLAG_EXISTS = None


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

    if cliswitch == 'local':
        cli += ' switch-local '
    else:
        cli += ' switch ' + cliswitch
    return cli


def check_cli(module, cli):
    """
    This method checks for idempotency using the vlag-show command.
    If a vlag with given vlag exists, return VLAG_EXISTS as True else False.
    :param module: The Ansible module to fetch input parameters
    :param cli: The CLI string
    :return Global Booleans: VLAG_EXISTS
    """
    name = module.params['pn_name']

    show = cli + ' vlag-show format name no-show-headers'
    show = shlex.split(show)
    out = module.run_command(show)[1]

    out = out.split()
    # Global flags
    global VLAG_EXISTS
    VLAG_EXISTS = True if name in out else False


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
    """ This section is for argument parsing """
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=False, type='str'),
            pn_clipassword=dict(required=False, type='str'),
            pn_cliswitch=dict(required=False, type='str', default='local'),
            pn_command=dict(required=True, type='str',
                            choices=['vlag-create', 'vlag-delete',
                                     'vlag-modify']),
            pn_name=dict(required=True, type='str'),
            pn_port=dict(type='str'),
            pn_peer_port=dict(type='str'),
            pn_mode=dict(type='str', choices=['active-standby', 'active-active']),
            pn_peer_switch=dict(type='str'),
            pn_failover_action=dict(type='str', choices=['move', 'ignore']),
            pn_lacp_mode=dict(type='str', choices=['off', 'passive', 'active']),
            pn_lacp_timeout=dict(type='str', choices=['slow', 'fast']),
            pn_lacp_fallback=dict(type='str', choices=['individual', 'bundled']),
            pn_lacp_fallback_timeout=dict(type='str')
        ),
        required_if=(
            ["pn_command", "vlag-create", ["pn_name", "pn_port", "pn_peer_port",
                                           "pn_peer_switch"]],
            ["pn_command", "vlag-delete", ["pn_name"]],
            ["pn_command", "vlag-modify", ["pn_name"]]
        )
    )

    # Argument accessing
    command = module.params['pn_command']
    name = module.params['pn_name']
    port = module.params['pn_port']
    peer_port = module.params['pn_peer_port']
    mode = module.params['pn_mode']
    peer_switch = module.params['pn_peer_switch']
    failover_action = module.params['pn_failover_action']
    lacp_mode = module.params['pn_lacp_mode']
    lacp_timeout = module.params['pn_lacp_timeout']
    lacp_fallback = module.params['pn_lacp_fallback']
    lacp_fallback_timeout = module.params['pn_lacp_fallback_timeout']

    # Building the CLI command string
    cli = pn_cli(module)

    if command == 'vlag-delete':

        check_cli(module, cli)
        if VLAG_EXISTS is False:
            module.exit_json(
                skipped=True,
                msg='VLAG with name %s does not exist' % name
            )
        cli += ' %s name %s ' % (command, name)


    else:

        if command == 'vlag-create':
            check_cli(module, cli)
            if VLAG_EXISTS is True:
                module.exit_json(
                    skipped=True,
                    msg='VLAG with name %s already exists' % name
                )
        cli += ' %s name %s ' % (command, name)

        if port:
            cli += ' port %s peer-port %s ' %(port, peer_port)

        if mode:
            cli += ' mode ' + mode

        if peer_switch:
            cli += ' peer-switch ' + peer_switch

        if failover_action:
            cli += ' failover-' + failover_action + '-L2 '

        if lacp_mode:
            cli += ' lacp-mode ' + lacp_mode

        if lacp_timeout:
            cli += ' lacp-timeout ' + lacp_timeout

        if lacp_fallback:
            cli += ' lacp-fallback ' + lacp_fallback

        if lacp_fallback_timeout:
            cli += ' lacp-fallback-timeout ' + lacp_fallback_timeout

    run_cli(module, cli)

# AnsibleModule boilerplate
from ansible.module_utils.basic import AnsibleModule

if __name__ == '__main__':
    main()

