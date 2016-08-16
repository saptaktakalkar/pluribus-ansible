#!/usr/bin/python
""" PN CLI vrouter-create/vrouter-delete/vrouter-modify """

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
module: pn_vrouter
author: "Pluribus Networks"
version: 1.0
short_description: CLI command to create/delete/modify a vrouter.
description:
  - Execute vrouter-create, vrouter-delete, vrouter-modify command.
  - Each fabric, cluster, standalone switch, or virtual network (VNET) can
    provide its tenants with a virtual router (vRouter) service that forwards
    traffic between networks and implements Layer 3 protocols.
  - C(vrouter-create) creates a new vRouter service.
  - C(vrouter-delete) deletes a vRouter service.
  - C(vrouter-modify) modifies a vRouter service.
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
      - Target switch(es) to run the CLI on.
    required: False
    type: str
  pn_command:
    description:
      - The C(pn_command) takes the vrouter command as value.
    required: true
    choices: ['vrouter-create', 'vrouter-delete', 'vrouter-modify']
    type: str
  pn_name:
    description:
      - Specify the name of the vRouter.
    required: true
    type: str
  pn_vnet:
    description:
      - Specify the name of the VNET.
      - Required for vrouter-create.
    type: str
  pn_service_type:
    description:
      - Specify if the vRouter is a dedicated or shared VNET service.
    choices: ['dedicated', 'shared']
    type: str
  pn_service_state:
    description:
      -  Specify to enable or disable vRouter service.
    choices: ['enable', 'disable']
    type: str
  pn_router_type:
    description:
      - Specify if the vRouter uses software or hardware.
      - Note that if you specify hardware as router type, you cannot assign IP
        addresses using DHCP. You must specify a static IP address.
    choices: ['hardware', 'software']
    type: str
  pn_hw_vrrp_id:
    description:
      - Specifies the VRRP ID for a hardware vrouter.
    type: str
  pn_router_id:
    description:
      - Specify the vRouter IP address.
    type: str
  pn_bgp_as:
    description:
      - Specify the Autonomous System Number(ASN) if the vRouter runs Border
        Gateway Protocol(BGP).
    type: int
  pn_bgp_redistribute:
    description:
      - Specify how BGP routes are redistributed.
    choices: ['static', 'connected', 'rip', 'ospf']
    type: str
  pn_bgp_max_paths:
    description:
      - Specify the maximum number of paths for BGP. This is a number between
        1 and 255 or 0 to unset.
    type: int
  pn_bgp_options:
    description:
      - Specify other BGP options as a whitespaces separted string within
        single quotes ''.
    type: str
  pn_rip_redistribute:
    description:
      - Specify how RIP routes are redistributed.
    choices: ['static', 'connected', 'ospf', 'bgp']
    type: str
  pn_ospf_redistribute:
    description:
      - Specify how OSPF routes are redistributed.
    choices: ['static', 'connected', 'bgp', 'rip']
    type: str
  pn_ospf_options:
    description:
      - Specify other OSPF options as a whitespaces separated string within
        single quotes ''.
    type: str
"""

EXAMPLES = """
- name: create vrouter
  pn_vrouter:
    pn_command: 'vrouter-create'
    pn_name: 'ansible-vrouter'
    pn_vnet: 'ansible-fab-global'
    pn_router_id: 208.74.182.1

- name: delete vrouter
  pn_vrouter:
    pn_command: 'vrouter-delete'
    pn_name: 'ansible-vrouter'
"""

RETURN = """
command:
  description: the CLI command run on the target node(s).
stdout:
  description: the set of responses from the vrouter command.
  returned: always
  type: list
stderr:
  description: the set of error responses from the vrouter command.
  returned: on error
  type: list
changed:
  description: Indicates whether the CLI caused changes on the target.
  returned: always
  type: bool
"""

VROUTER_EXISTS = None
VROUTER_NAME_EXISTS = None


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
    A switch can have only one vRouter configuration.
    If a vRouter already exists on the given switch, return VROUTER_EXISTS as
    True else False.
    If a vRouter with the given name exists(on a different switch), return
    VROUTER_NAME_EXISTS as True else False.

    :param module: The Ansible module to fetch input parameters
    :param cli: The CLI string
    :return Global Booleans: VROUTER_EXISTS, VROUTER_NAME_EXISTS
    """
    name = module.params['pn_name']
    # Global flags
    global VROUTER_EXISTS, VROUTER_NAME_EXISTS

    # Get the name of the local switch
    location = cli + ' switch-setup-show format switch-name'
    location = location.split()[1]

    # Check for any vRouters on the switch
    check_vrouter = cli + ' vrouter-show location %s ' % location
    check_vrouter += 'format name no-show-headers'
    check_vrouter = shlex.split(check_vrouter)
    out = module.run_command(check_vrouter)[1]

    VROUTER_EXISTS = True if out else False


    # Check for any vRouters with the given name
    show = cli + ' vrouter-show format name no-show-headers '
    show = shlex.split(show)
    out = module.run_command(show)[1]
    out = out.split()

    VROUTER_NAME_EXISTS = True if name in out else False


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
    """ This section is for arguments parsing """
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=False, type='str'),
            pn_clipassword=dict(required=False, type='str'),
            pn_cliswitch=dict(required=False, type='str', default='local'),
            pn_command=dict(required=True, type='str',
                            choices=['vrouter-create', 'vrouter-delete',
                                     'vrouter-modify']),
            pn_name=dict(required=True, type='str'),
            pn_vnet=dict(type='str'),
            pn_service_type=dict(type='str', choices=['dedicated', 'shared']),
            pn_service_state=dict(type='str', choices=['enable', 'disable']),
            pn_router_type=dict(type='str', choices=['hardware', 'software']),
            pn_hw_vrrp_id=dict(type='str'),
            pn_router_id=dict(type='str'),
            pn_bgp_as=dict(type='int'),
            pn_bgp_redistribute=dict(type='str', choices=['static', 'connected',
                                                          'rip', 'ospf']),
            pn_bgp_max_paths=dict(type='int'),
            pn_bgp_options=dict(type='str'),
            pn_rip_redistribute=dict(type='str', choices=['static', 'connected',
                                                          'bgp', 'ospf']),
            pn_ospf_redistribute=dict(type='str', choices=['static', 'connected',
                                                           'bgp', 'rip']),
            pn_ospf_options=dict(type='str'),
            pn_vrrp_track_port=dict(type='str')
        ),
        required_if=(
            ["pn_command", "vrouter-create", ["pn_name", "pn_vnet"]],
            ["pn_command", "vrouter-delete", ["pn_name"]],
            ["pn_command", "vrouter-modify", ["pn_name"]]
        )
    )

    # Accessing the arguments
    command = module.params['pn_command']
    name = module.params['pn_name']
    vnet = module.params['pn_vnet']
    service_type = module.params['pn_service_type']
    service_state = module.params['pn_service_state']
    router_type = module.params['pn_router_type']
    hw_vrrp_id = module.params['pn_hw_vrrp_id']
    router_id = module.params['pn_router_id']
    bgp_as = module.params['pn_bgp_as']
    bgp_redistribute = module.params['pn_bgp_redistribute']
    bgp_max_paths = module.params['pn_bgp_max_paths']
    bgp_options = module.params['pn_bgp_options']
    rip_redistribute = module.params['pn_rip_redistribute']
    ospf_redistribute = module.params['pn_ospf_redistribute']
    ospf_options = module.params['pn_ospf_options']
    vrrp_track_port = module.params['pn_vrrp_track_port']

    # Building the CLI command string
    cli = pn_cli(module)

    if command == 'vrouter-delete':
        check_cli(module, cli)
        if VROUTER_NAME_EXISTS is False:
            module.exit_json(
                skipped=True,
                msg='vRouter with name %s does not exist' % name
            )
        cli += ' %s name %s ' % (command, name)

    else:

        if command == 'vrouter-create':
            check_cli(module, cli)
            if VROUTER_EXISTS is True:
                module.exit_json(
                    skipped=True,
                    msg='Maximum number of vRouters has been reached on this '
                        'switch'
                )
            if VROUTER_NAME_EXISTS is True:
                module.exit_json(
                    skipped=True,
                    msg='vRouter with name %s already exists' % name
                )
        cli += ' %s name %s ' % (command, name)

        if vnet:
            cli += ' vnet ' + vnet

        if service_type:
            cli += ' %s-vnet-service ' % service_type

        if service_state:
            cli += ' ' + service_state

        if router_type:
            cli += ' router-type ' + router_type

        if hw_vrrp_id:
            cli += ' hw-vrrp-id ' + hw_vrrp_id

        if router_id:
            cli += ' router-id ' + router_id

        if bgp_as:
            cli += ' bgp-as ' + str(bgp_as)

        if bgp_redistribute:
            cli += ' bgp-redistribute ' + bgp_redistribute

        if bgp_max_paths:
            cli += ' bgp-max-paths ' + str(bgp_max_paths)

        if bgp_options:
            cli += ' %s ' % bgp_options

        if rip_redistribute:
            cli += ' rip-redistribute ' + rip_redistribute

        if ospf_redistribute:
            cli += ' ospf-redistribute ' + ospf_redistribute

        if ospf_options:
            cli += ' %s ' % ospf_options

        if vrrp_track_port:
            cli += ' vrrp-track-port ' + vrrp_track_port

    run_cli(module, cli)

# AnsibleModule boilerplate
from ansible.module_utils.basic import AnsibleModule

if __name__ == '__main__':
    main()

