#!/usr/bin/python
""" PN CLI show commands """

import subprocess
import shlex

DOCUMENTATION = """
---
module: pn_show
author: "Pluribus Networks"
short_description: Run show commands on nvOS device
description:
  - Execute show command in the nodes and returns the results
    read from the device.
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
    - Target switch to run the cli on.
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
        output. List of comman separated parameters
    type: str
  pn_options:
    description:
      - Specify formatting options.
  pn_quiet:
    description:
      - The C(pn_quiet) option to enable or disable the initial system message
    required: false
    type: bool
    default: true
"""

EXAMPLES = """
- name: run the vlan-show command
  pn_show:
    pn_cliusername: admin
    pn_clipassword: admin
    pn_command: 'vlan-show'
    pn_parameters: id,scope,ports
    pn_options: 'layout vertical'

- name: run the vlag-show command
  pn_show:
    pn_cliusername: admin
    pn_clipassword: admin
    pn_command: 'vlag-show'
    pn_parameters: 'id,name,cluster,mode'
    pn_options: 'no-show-headers'

- name: run the cluster-show command
  pn_show:
    pn_cliusername: admin
    pn_clipassword: admin
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
rc:
  description: return code of the module.
  returned: 0 for output, 1 for error, 2 for no show.
  type: int
changed:
  description: Indicates whether the CLI caused any change on the target.
  returned: always(False)
  type: bool
"""


def main():
    """ This section is for arguments parsing """
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=True, type='str',
                                aliases=['username']),
            pn_clipassword=dict(required=True, type='str', aliase=['password']),
            pn_cliswitch=dict(required=False, type='str', aliases=['switch']),
            pn_command=dict(required=True, type='str', aliases=['command']),
            pn_parameters=dict(default='all', type='str',
                               aliases=['parameters']),
            pn_options=dict(type='str', aliases=['options']),
            pn_quiet=dict(default=True, type='bool', aliases=['quiet'])
        )
    )

    # Accessing the arguments
    cliusername = module.params['pn_cliusername']
    clipassword = module.params['pn_clipassword']
    cliswitch = module.params['pn_cliswitch']
    command = module.params['pn_command']
    parameters = module.params['pn_parameters']
    options = module.params['pn_options']
    quiet = module.params['pn_quiet']

    # Building the CLI command string
    if quiet is True:
        cli = ('/usr/bin/cli --quiet --user ' + cliusername + ':' +
               clipassword)
    else:
        cli = '/usr/bin/cli --user ' + cliusername + ':' + clipassword

    if cliswitch:
        cli += ' switch ' + cliswitch

    cli += ' ' + command
    if parameters:
        cli += ' format ' + parameters

    if options:
        cli += ' ' + options

    # Run the CLI command
    showcmd = shlex.split(cli)
    response = subprocess.Popen(showcmd, stderr=subprocess.PIPE,
                                stdout=subprocess.PIPE, universal_newlines=True)
    # 'out' contains the output
    # 'err; contains the error message
    out, err = response.communicate()

    # Response in JSON format
    if err:
        module.exit_json(
            command=cli,
            stderr=err.strip("\r\n"),
            rc=1,
            changed=False
        )

    if out:
        module.exit_json(
            command=cli,
            stdout=out.strip("\r\n"),
            rc=0,
            changed=False
        )

    else:
        module.exit_json(
            command=cli,
            msg="Nothing to display!!!",
            rc=2,
            changed=False
        )

# AnsibleModule boilerplate
from ansible.module_utils.basic import AnsibleModule

if __name__ == '__main__':
    main()

