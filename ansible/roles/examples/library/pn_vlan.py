#!/usr/bin/python
""" PN CLI vlan-create/vlan-delete """

import subprocess
import shlex

DOCUMENTATION = """
---
module: pn_vlan
author: "Pluribus Networks"
short_description: CLI command to create/delete a vlan.
description:
  - Execute vlan-create or vlan-delete command. 
  - Requires vlan id:
    - id should be in the range 2...4092.
  - If vlan-create, scope is required. Scope can be fabric/local. 
  - Can provide options for vlan-create.
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
  pn_vlancommand:
    description:
      - The C(pn_vlancommand) takes the vlan-create/delete command as value.
    required: true
    choices: vlan-create, vlan-delete
    type: str
  pn_vlanid:
    description:
      - The VLAN id. ID should be in the range 2...4092.
    required: true
    type: int
  pn_vlanscope:
    description:
      - Scope for the VLAN(fabric/local). Required when creating a vlan.
    required_if: vlan-create
    choices: fabric/local
    type: str
  pn_vlandesc:
    description:
      - Description for the VLAN.
    required: False
    type: str
  pn_vlanstats:
    description:
      - Enalble/disable stats
    required: False
    choices: stats/no-stats
    type: str
  pn_vlanports:
    description:
      - List of ports for the VLAN, comma separated.
    required: False
    type: str
  pn_vlanuntaggedports:
    description:
      - List of untagged ports for the VLAN, comma separated.
    required: False
    type: str
  pn_quiet:
    description:
      - The C(pn_quiet) option to enable or disable the system bootup message.
    required: false
    type: bool
    default: true
"""

EXAMPLES = """
- name: create a VLAN
  pn_vlan:
    pn_cliusername: admin
    pn_clipassword: admin
    pn_vlancommand: 'vlan-create'
    pn_vlanid: 1854
    pn_vlanscope: 'local'
    pn_quiet: True

- name: delete VLANs
  pn_vlan:
    pn_cliusername: admin
    pn_clipassword: admin
    pn_vlancommand: 'vlan-delete'
    pn_vlanid: 1854
    pn_quiet: True
"""

RETURN = """
vlancmd:
  description: the CLI command run on the target node(s).
stdout:
  description: the set of responses from the vlan command.
  returned: always
  type: list
stdout_lines:
  description: the value of stdout split into a list.
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
            pn_vlancommand=dict(required=True, type='str',
                                choices=['vlan-create', 'vlan-delete']),
            pn_vlanid=dict(required=True, type='int'),
            pn_vlanscope=dict(type='str', choices=['fabric', 'local']),
            pn_vlandesc=dict(required=False, type='str'),
            pn_vlanstats=dict(required=False, type='str',
                              choices=['stats', 'no-stats']),
            pn_vlanports=dict(required=False, type='str'),
            pn_vlanuntaggedports=dict(required=False, type='str'),
            pn_quiet=dict(default=True, type='bool')
        ),
        required_if=(
            ["pn_vlancommand", "vlan-create", ["pn_vlanid", "pn_vlanscope"]],
            ["pn_vlancommand", "vlan-delete", ["pn_vlanid"]]
        )
    )

    # Accessing the arguments
    cliusername = module.params['pn_cliusername']
    clipassword = module.params['pn_clipassword']
    vlancommand = module.params['pn_vlancommand']
    vlanid = module.params['pn_vlanid']
    vlanscope = module.params['pn_vlanscope']
    vlandesc = module.params['pn_vlandesc']
    vlanstats = module.params['pn_vlanstats']
    vlanports = module.params['pn_vlanports']
    vlanuntaggedports = module.params['pn_vlanuntaggedports']
    quiet = module.params['pn_quiet']

    # Building the CLI command string
    if quiet is True:
        cli = ('/usr/bin/cli --quiet --user ' + cliusername + ':' +
               clipassword + ' ')
    else:
        cli = '/usr/bin/cli --user ' + cliusername + ':' + clipassword + ' '

    if vlanid < 2 | vlanid > 4092:
        module.fail_json(msg="Invalid vlan ID")

    cli += vlancommand + ' id ' + str(vlanid)

    if vlanscope:
        cli += ' scope ' + vlanscope

    if vlandesc:
        cli += ' description ' + vlandesc

    if vlanstats:
        cli += ' stats ' + vlanstats

    if vlanports:
        cli += ' ports ' + vlanports

    if vlanuntaggedports:
        cli += ' untagged-ports ' + vlanuntaggedports

    # Run the CLI command
    vlancmd = shlex.split(cli)
    response = subprocess.Popen(vlancmd, stderr=subprocess.PIPE,
                                stdout=subprocess.PIPE, universal_newlines=True)

    # 'out' contains the output
    # 'err' contains the error messages
    out, err = response.communicate()

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
