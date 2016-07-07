#!/usr/bin/python
# Test PN CLI show
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
  pn_showcommand:
    description:
      - The C(pn_showcommand) takes a CLI command as value which
        is executed on the nodes and the result is returned.
    required: true
    type: str
  pn_showoptions:
    description:
      - The C(pn_showoptions) takes space-delimited output formatting options.
    required: false
    type: str
    default: ' '
  pn_quiet:
    description:
      - The C(pn_quiet) option to enable or disable the initial system message
    required: false
    type: bool
    default: true
"""

EXAMPLES = """
- name: run the vlan-show CLI command
  pn_show:
    pn_cliusername: admin
    pn_clipassword: admin
    pn_showcommand: 'vlan-show'
    pn_quiet: True

- name: run the vlag-show CLI command
  pn_show:
    pn_cliusername: admin
    pn_clipassword: admin
    pn_showcommand: 'vlag-show'
    pn_showoptions: 'format id,name,cluster,mode'
    pn_quiet: False

- name: run the cluster-show command
  pn_show:
    pn_cliusername: admin
    pn_clipassword: admin
    pn_showcommand: 'cluster-show'
    pn_showoptions: 'layout vertical'
    pn_quiet: True
"""

RETURN = """
showcmd:
  description: the CLI command run on the target node(s).
stdout:
  description: the set of responses from the show command.
  returned: always
  type: list
stdout_lines:
  description: the value of stdout split into a list.
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


def main():
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=True, type='str'),
            pn_clipassword=dict(required=True, type='str'),
            pn_showcommand=dict(required=True, type='str'),
            pn_showoptions=dict(default=' '),
            pn_quiet=dict(default=True, type='bool')
        )
    )

    cliusername = module.params['pn_cliusername']
    clipassword = module.params['pn_clipassword']
    command = module.params['pn_showcommand']
    options = module.params['pn_showoptions']
    quiet = module.params['pn_quiet']

    if quiet is True:
        show = ('/usr/bin/cli --quiet --user ' + cliusername + ':' +
                clipassword + ' ' + command)
    else:
        show = ('/usr/bin/cli --user ' + cliusername + ':' +
                clipassword + ' ' + command)

    if options != ' ':
        show += ' ' + options

    showcmd = shlex.split(show)
    response = subprocess.Popen(showcmd, stderr=subprocess.PIPE,
                                stdout=subprocess.PIPE, universal_newlines=True)
    out, err = response.communicate()

    if out:
        module.exit_json(
            showcmd=show,
            stdout=out.strip("\r\n"),
            changed=False
        )

    if err:
        module.exit_json(
            showcmd=show,
            stderr=err.strip("\r\n"),
            changed=False
        )

from ansible.module_utils.basic import AnsibleModule

if __name__ == '__main__':
    main()
