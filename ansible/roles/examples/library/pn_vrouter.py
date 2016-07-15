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
  - Requires vrouter name:
    - Alphanumeric characters
    - Special characters like: _
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
  pn_vroutercommand:
    description:
      - The C(pn_vroutercommand) takes the v-router command as value.
    required: true
    choices: vrouter-create, vrouter-delete, vrouter-modify
    type: str
  pn_vroutername:
    description:
      - name for service configuration.
    required: true
    type: str
  pn_vroutervnet:
    description:
      - vnet assigned to the service
    required_if: vrouter-create 
    type: str
  pn_vrouterstate:
    description:
      - state of service
    required_if: vrouter-create
    type: str
  pn_vrouterhw_vrrp_id:
    description:
      - vrrp id assigned to the hardware vrouter
    required_if: vrouter_create
    type: int
  pn_vrouterbgp_as: 
    description: 
      - BGP Autonomous System number from 1 to 4294967295
      required: False
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
    pn_routercommand: 'vrouter-create'
    pn_vroutername: 'ansible-vrouter'
    pn_vroutervnet: 'ansible-vnet'
    pn_vrouterstate: 'enable'
    pn_vrouterhw_vrrp_id: 18
    pn_quiet: True

- name: delete vrouter 
  pn_vrouter:
    pn_cliusername: admin
    pn_clipassword: admin
    pn_vroutercommand: 'vrouter-delete'
    pn_vroutername: 'ansible-vrouter'
    pn_quiet: True
"""

RETURN = """
vroutercmd:
  description: the CLI command run on the target node(s).
stdout:
  description: the set of responses from the vrouter command.
  returned: always
  type: list
stdout_lines:
  description: the value of stdout split into a list.
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
            pn_cliusername=dict(required=True, type='str'),
            pn_clipassword=dict(required=True, type='str'),
            pn_vroutercommand=dict(required=True, type='str',
                                   choices=['vrouter-create', 'vrouter-delete',
                                            'vrouter-modify']),
            pn_vroutername=dict(required=True, type='str'),
            pn_vroutervnet=dict(type='str'),
            pn_vrouterstate=dict(type='str', choices=['enable', 'disable']),
            pn_vrouterbgp_as=dict(required=False, type='str'),
            pn_vrouterhw_vrrp_id=dict(required=False, type='int'),
            pn_quiet=dict(default=True, type='bool')
        ),
        required_if=(
            ["pn_vroutercommand", "vrouter-create",
             ["pn_vroutername", "pn_vroutervnet", "pn_vrouterstate",
              "pn_vrouterhw_vrrp_id"]],
            ["pn_vroutercommand", "vrouter-delete", ["pn_vroutername"]],
            ["pn_vroutercommand", "vrouter-modify", ["pn_vroutername"]]
        )
    )

    # Accessing the arguments
    cliusername = module.params['pn_cliusername']
    clipassword = module.params['pn_clipassword']
    vroutercommand = module.params['pn_vroutercommand']
    vroutername = module.params['pn_vroutername']
    vroutervnet = module.params['pn_vroutervnet']
    vrouterstate = module.params['pn_vrouterstate']
    vrouterbgp_as = module.params['pn_vrouterbgp_as']
    vrouterhw_vrrp_id = module.params['pn_vrouterhw_vrrp_id']
    quiet = module.params['pn_quiet']

    # Building the CLI command string
    if quiet is True:
        cli = ('/usr/bin/cli --quiet --user ' + cliusername + ':' +
               clipassword + ' ')
    else:
        cli = '/usr/bin/cli --user ' + cliusername + ':' + clipassword + ' '

    if vroutername:
        cli += vroutercommand + ' name ' + vroutername

    if vroutervnet:
        cli += ' vnet ' + vroutervnet

    if vrouterbgp_as:
        cli += ' bgp-as ' + vrouterbgp_as

    if vrouterhw_vrrp_id:
        cli += ' hw-vrrp-id ' + str(vrouterhw_vrrp_id)

    if vrouterstate:
        cli += " " + vrouterstate

    # Run the CLI command
    vroutercmd = shlex.split(cli)
    response = subprocess.Popen(vroutercmd, stderr=subprocess.PIPE,
                                stdout=subprocess.PIPE, universal_newlines=True)

    # 'out' contains the output
    # 'err' contains the error messages
    out, err = response.communicate()

    if err:
        module.exit_json(
            vroutercmd=vrouter,
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
