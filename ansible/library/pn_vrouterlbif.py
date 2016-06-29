#!/usr/bin/python
# Test PN CLI vrouter-loopback-interface-add/remove/modify
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
from ansible.module_utils.basic import *

DOCUMENTATION = """
---
module: pn_vrouterlbif
author: "Pluribus Networks"
short_description: CLI command to add/remove/modify vrouter-loopback-interface
description:
  - Execute vrouter-loopback-interface-add, vrouter-loopback-interface-remove,
    vrouter-loopback-interface-modify commands.
  - Add/remove/modify loopback interface for a vrouter
options:
  pn_cliusername:
    description:
      - Login username.
    required: true
    type: str
  pn_clipassword
    description:
      - Login password.
    required: true
    type: str
  pn_vrouterlbcommand:
    description:
      - The C(pn_vrouterlbcommand) takes the vrouter-loopback-interface command
        as value.
    required: true
    choices: vrouter-loopback-interface-add, vrouter-loopback-interface-remove,
             vrouter-loopback-interface-modify
    type: str
  pn_vrouterlbname:
    description:
      - The C(pn_vrouterlbname) takes a valid name for service configuration.
    required: true
    type: str
  pn_vrouterlbindex:
    description:
      - loopback index from 1 to 255
    required_if: vrouter-loopback-interface-add/remove
    type: int
  pn_vrouterlbip:
    description:
      - loopback IP address
    required_if: vrouter-loopback-interface-add
    type: str
  pn_quiet:
    description:
      - The C(pn_quiet) option to enable or disable the system bootup message
    required: false
    type: bool
    default: true
"""

EXAMPLES = """
- name: add vrouter-loopback-interface
  pn_vrouterlbif:
    pn_cliusername: admin pn_clipassword: admin
    pn_vrouterlbcommand: 'vrouter-loopback-interface-add'
    pn_vrouterlbname: 'self'
    pn_vrouterlbindes: 10
    pn_vrouterlbip: 104.104.104.1
    pn_quiet: True
- name: remove vrouter-loopback-interface
  pn_vrouterlbif:
    pn_cliusername: admin
    pn_clipassword: admin
    pn_vrouterlbcommand: 'vrouter-loopback-interface-remove'
    pn_vrouterlbname: 'self'
    pn_quiet: True
"""

RETURN = """
vrouterlbcmd:
  description: the CLI command run on the target node(s).
stdout:
  description: the set of responses from the vrouterlb command.
  returned: always
  type: list
stdout_lines:
  description: the value of stdout split into a list.
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
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=True, type='str'),
            pn_clipassword=dict(required=True, type='str'),
            pn_vrouterlbcommand=dict(required=True, type='str',
                                     choices=['vrouter-create',
                                              'vrouter-delete',
                                              'vrouter-modify']),
            pn_vrouterlbname=dict(required=True, type='str'),
            pn_vrouterlbindex=dict(required=False, type='int'),
            pn_vrouterlbip=dict(required=False, type='str'),
            pn_quiet=dict(default=True, type='bool')
        ),
        required_if=(
            ["pn_vrouterlbcommand", "vrouter-loopback-interface-add",
             ["pn_vrouterlbname", "pn_vrouterlbindex", "pn_vrouterlbip"]],
            ["pn_vrouterlbcommand", "vrouter-loopback-interface-remove",
             ["pn_vrouterlbname", "pn_vrouterlbindex"]],
            ["pn_vrouterlbcommand", "vrouter-loopback-interface-modify",
             ["pn_vrouterlbname"]]
        )
    )

    cliusername = module.params['pn_cliusername']
    clipassword = module.params['pn_clipassword']
    vrouterlbcommand = module.params['pn_vrouterlbcommand']
    vrouterlbname = module.params['pn_vrouterlbname']
    vrouterlbindex = module.params['pn_vrouterlbindex']
    vrouterlbip = module.params['pn_vrouterlbip']
    quiet = module.params['pn_quiet']

    if quiet is True:
        cli = ('/usr/bin/cli --quiet --user ' + cliusername + ':' +
               clipassword + ' ')
    else:
        cli = '/usr/bin/cli --user ' + cliusername + ':' + clipassword + ' '

    vrouterlb = cli

    if vrouterlbname:
        vrouterlb = cli + vrouterlbcommand + ' vrouter-name ' + vrouterlbname

    if vrouterlbindex:
        vrouterlb += ' index ' + str(vrouterlbindex)

    if vrouterlbip:
        vrouterlb += ' ip ' + vrouterlbip

    vrouterlbcmd = shlex.split(vrouterlb)
    response = subprocess.Popen(vrouterlbcmd, stderr=subprocess.PIPE,
                                stdout=subprocess.PIPE, universal_newlines=True)
    out, err = response.communicate()

    if out:
        module.exit_json(
            vrouterlbcmd=vrouterlb,
            stdout=out.rstrip("\r\n"),
            changed=True
        )

    if err:
        module.exit_json(
            vrouterlbcmd=vrouterlb,
            stderr=err.rstrip("\r\n"),
            changed=False
        )

if __name__ == '__main__':
    main()
