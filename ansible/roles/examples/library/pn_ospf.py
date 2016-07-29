#!/usr/bin/python
""" PN-CLI vrouter-ospf-add/remove """

import subprocess
import shlex

DOCUMENTATION = """
---
module: pn_ospf
author: "Pluribus Networks"
short_description: CLI command to add/remove ospf protocol to a vrouter
description:
  - Execute vrouter-ospf-add, vrouter-ospf-remove command.
  - This command adds/removes Open Shortest Path First(OSPF) routing
    protocol to a virtual router(vRouter) service.
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
      - The C(pn_command) takes the vrouter-ospf add/remove
        command as value.
    required: true
    choices: vrouter-ospf-add, vrouter-ospf-remove
    type: str
  pn_vrouter_name:
    description:
      - specify the name of the vRouter.
    required: true
    type: str
  pn_network_ip:
    description:
      - Specify the network IP address.
    required_if: vrouter-ospf-add
    type: str
  pn_netmask:
    description:
      - Specify the netmask of the IP address.
    required_if: vrouter-ospf-add
    type: str
  pn_ospf_area:
    description:
    - Stub area number for the configuration
    required_if: vrouter-ospf-add
    type: str
  pn_quiet:
    description:
    - Enable/disable system information
    required: false
    type: bool
    default: true
"""

EXAMPLES = """
- name: "Add OSPF to vrouter"
  pn_ospf:
    pn_cliusername: admin
    pn_clipassword: admin
    pn_command: vrouter-ospf-add
    pn_vrouter_name: name-string
    pn_network_ip: 192.168.11.2/24
    pn_ospf_area: 1.0.0.0

- name: "Remove OSPF from vrouter"
  pn_ospf:
    pn_cliusername: admin
    pn_clipassword: admin
    pn_command: vrouter-ospf-remove
    pn_vrouter_name: name-string
"""

RETURN = """
command:
  description: the CLI command run on the target node(s).
stdout:
  description: the set of responses from the ospf command.
  returned: always
  type: list
stderr:
  description: the set of error responses from the ospf command.
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
                            choices=['vrouter-ospf-add',
                                     'vrouter-ospf-remove']),
            pn_vrouter_name=dict(required=True, type='str'),
            pn_network_ip=dict(type='str'),
            pn_netmask=dict(type='str'),
            pn_ospf_area=dict(type='str'),
            pn_quiet=dict(default=True, type='bool')
        ),
        required_if=(
            ['pn_command', 'vrouter-ospf-add',
             ['pn_network_ip', 'pn_netmask', 'pn_ospf_area']],
            ['pn_command', 'vrouter-ospf-remove', ['pn_network_ip']]
        )
    )

    # Accessing the arguments
    cliusername = module.params['pn_cliusername']
    clipassword = module.params['pn_clipassword']
    cliswitch = module.params['pn_cliswitch']
    command = module.params['pn_command']
    vrouter_name = module.params['pn_vrouter_name']
    network_ip = module.params['pn_network_ip']
    netmask = module.params['pn_netmask']
    ospf_area = module.params['pn_ospf_area']
    quiet = module.params['pn_quiet']

    # Building the CLI command string
    if quiet is True:
        cli = ('/usr/bin/cli --quiet --user ' + cliusername + ':' +
               clipassword)
    else:
        cli = '/usr/bin/cli --user ' + cliusername + ':' + clipassword


    if cliswitch:
        if cliswitch == 'local':
            cli += ' switch-local '
        else:
            cli += ' switch ' + cliswitch

    cli += ' ' + command + ' vrouter-name ' + vrouter_name

    if network_ip:
        cli += ' network ' + network_ip

    if netmask:
        cli += ' netmask ' + netmask

    if ospf_area:
        cli += ' ospf-area ' + ospf_area

    # Run the CLI command
    ospfcommand = shlex.split(cli)
    response = subprocess.Popen(ospfcommand, stderr=subprocess.PIPE,
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

