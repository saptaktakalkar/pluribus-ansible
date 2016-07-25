#!/usr/bin/python
""" PN CLI vrouter-create/vrouter-delete/vrouter-modify """

import subprocess
import shlex

DOCUMENTATION = """
---
module: pn_vrouter
author: "Pluribus Networks"
short_description: CLI command to create/delete/modify a vrouter
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
      - Login username
    required: true
    type: str
  pn_clipassword:
    description:
      - Login password
    required: true
    type: str
  pn_cliswitch:
    description:
      - Target switch to run the CLI on.
    required: False
    type: str
  pn_command:
    description:
      - The C(pn_command) takes the v-router command as value.
    required: true
    choices: vrouter-create, vrouter-delete, vrouter-modify
    type: str
  pn_name:
    description:
      - Specify the name of the vRouter.
    required: true
    type: str
  pn_vnet:
    description:
      - Specify the name of the VNET.
    required_if: vrouter-create
    type: str
  pn_service_type:
    description:
      - Specify if the vRouter is a dedicated or shared VNET service.
    choices: dedicated, shared
    type: str
  pn_service_state:
    description:
      -  Specify to enable or disable vRouter service.
    choices: enable, disable
    type: str
  pn_router_type:
    description:
      - Specify if the vRouter uses software or hardware.
      - Note that if you specify hardware as router type, you cannot assign IP
        addresses using DHCP. You must specify a static IP address.
    choices: hardware, software
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
  pn_quiet:
    description:
      - The C(pn_quiet) option to enable or disable the system bootup message
    required: false
    type: bool
    default: true
"""

EXAMPLES = """
- name: create vrouter
  pn_vrouter:
    pn_cliusername: admin
    pn_clipassword: admin
    pn_command: 'vrouter-create'
    pn_name: 'ansible-vrouter'
    pn_vnet: 'ansible-vnet'
    pn_router_id: 208.74.182.1

- name: delete vrouter
  pn_vrouter:
    pn_cliusername: admin
    pn_clipassword: admin
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


def main():
    """ This section is for arguments parsing """
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=True, type='str',
                                aliases=['username']),
            pn_clipassword=dict(required=True, type='str',
                                aliases=['password']),
            pn_cliswitch=dict(required=False, type='str', aliases=['switch']),
            pn_command=dict(required=True, type='str',
                            choices=['vrouter-create', 'vrouter-delete',
                                     'vrouter-modify'], aliases=['command']),
            pn_name=dict(required=True, type='str', aliases=['name']),
            pn_vnet=dict(type='str', aliases=['vnet']),
            pn_service_type=dict(type='str', choices=['dedicated', 'shared'],
                                 aliases=['service_type']),
            pn_service_state=dict(type='str', choices=['enable', 'disable'],
                                  aliases=['service_state']),
            pn_router_type=dict(type='str', choices=['hardware', 'software'],
                                aliases=['router_type']),
            pn_hw_vrrp_id=dict(type='str', aliases=['hw_vrrp_id']),
            pn_router_id=dict(type='str', aliases=['router_id']),
            pn_bgp_as=dict(type='int', aliases=['bgp_as']),
            pn_quiet=dict(default=True, type='bool', aliases=['quiet'])
        ),
        required_if=(
            ["pn_command", "vrouter-create",
             ["pn_name", "pn_vnet", "pn_service_state", "pn_hw_vrrp_id"]],
            ["pn_command", "vrouter-delete", ["pn_name"]],
            ["pn_command", "vrouter-modify", ["pn_name"]]
        )
    )

    # Accessing the arguments
    cliusername = module.params['pn_cliusername']
    clipassword = module.params['pn_clipassword']
    cliswitch = module.params['pn_cliswitch']
    command = module.params['pn_command']
    name = module.params['pn_name']
    vnet = module.params['pn_vnet']
    service_type = module.params['pn_service_type']
    service_state = module.params['pn_service_state']
    router_type = module.params['pn_router_type']
    hw_vrrp_id = module.params['pn_hw_vrrp_id']
    router_id = module.params['pn_router_id']
    bgp_as = module.params['pn_bgp_as']
    quiet = module.params['pn_quiet']

    # Building the CLI command string
    if quiet is True:
        cli = ('/usr/bin/cli --quiet --user ' + cliusername + ':' +
               clipassword + ' ')
    else:
        cli = '/usr/bin/cli --user ' + cliusername + ':' + clipassword + ' '

    if cliswitch:
        cli += ' switch ' + cliswitch

    cli += ' ' + command + ' name ' + name

    if vnet:
        cli += ' vnet ' + vnet

    if service_type:
        cli += ' ' + service_type + '-vnet-service '

    if service_state:
        cli += ' ' + service_state

    if router_type:
        cli += ' router-type ' + router_type

    if hw_vrrp_id:
        cli += ' hw-vrrp-id ' + hw_vrrp_id

    if router_id:
        cli += ' router-id ' + router_id

    if bgp_as:
        cli += ' bgp-as ' + bgp_as

    # Run the CLI command
    vroutercmd = shlex.split(cli)
    response = subprocess.Popen(vroutercmd, stderr=subprocess.PIPE,
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

