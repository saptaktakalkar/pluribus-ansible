#!/usr/bin/python
""" PN-CLI module for fabric-create/fabric-join"""

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


import shlex
import subprocess


def main():
    """Module instantiation"""
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=True, type='str'),
            pn_clipassword=dict(required=True, type='str'),
            pn_command=dict(required=True, type='str',
                            choices=["fabric-create", "fabric-join"]),
            pn_fabric_name=dict(required=True, type='str'),
            pn_quiet=dict(default=True, type='bool')
        )
    )

    # Accessing arguments
    cliusername = module.params["pn_cliusername"]
    clipassword = module.params["pn_clipassword"]
    command = module.params["pn_command"]
    fabric_name = module.params["pn_fabric_name"]
    quiet = module.params["pn_quiet"]

    # Building the CLI
    cli = '/usr/bin/cli '
    if quiet is True:
        cli += ' --quiet '

    cli += ' --user %s:%s ' % (cliusername, clipassword)

    cli += ' %s name %s ' % (command, fabric_name)

    # Running the CLI
    command = shlex.split(cli)
    response = subprocess.Popen(command, stderr=subprocess.PIPE,
                                stdout=subprocess.PIPE, universal_newlines=True)
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
