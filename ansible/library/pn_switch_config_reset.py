#!/usr/bin/python
""" PN CLI Switch Config Reset """

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

from ansible.module_utils.basic import AnsibleModule
import shlex

DOCUMENTATION = """
---
module: pn_switch_config_reset
author: 'Pluribus Networks (@saptaktakalkar)'
version: 1
short_description: CLI command to reset a switch.
description:
    This module will reset a switch by running switch-config-reset command.
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
"""

EXAMPLES = """
- name: Switch config reset
  pn_switch_config_reset:
    pn_cliusername: "{{ USERNAME }}"
    pn_clipassword: "{{ PASSWORD }}"
"""

RETURN = """
msg:
  description: String describing if switch reset was successful or not.
  returned: always
  type: str
changed:
  description: Indicates whether the CLI caused changes on the target.
  returned: always
  type: bool
"""


def main():
    """ This section is for arguments parsing """
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=False, type='str'),
            pn_clipassword=dict(required=False, type='str', no_log=True)
        )
    )

    username = module.params['pn_cliusername']
    password = module.params['pn_clipassword']

    if username and password:
        cli = '/usr/bin/cli --quiet --user %s:%s ' % (username, password)
    else:
        cli = '/usr/bin/cli --quiet '

    cli += ' --no-login-prompt switch-config-reset '

    cli = shlex.split(cli)
    rc, out, err = module.run_command(cli)

    if err:
        module.exit_json(
            error='1',
            failed=True,
            stderr=err.strip(),
            msg='Operation Failed: ' + str(cli),
            changed=False
        )
    else:
        module.exit_json(
            msg='Switch Config Reset Successful.',
            error='0',
            failed=False,
            changed=True
        )


if __name__ == '__main__':
    main()

