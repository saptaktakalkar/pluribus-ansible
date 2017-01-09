#!/usr/bin/python
""" Tests for ZTP L3 """

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

DOCUMENTATION = """
---
module: pn_test_ztp_l3
author: "Pluribus Networks (@saptaktakalkar)"
version: 1
short_description: Tests for ZTP L3.
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

RETURN = """
msg:
  description: The set of responses for each command.
  returned: always
  type: str
changed:
  description: Indicates whether the CLI caused changes on the target.
  returned: always
  type: bool
"""


def pn_cli(module):
    """
    This method is to generate the cli portion to launch the Netvisor cli.
    It parses the username, password, switch parameters from module.
    :param module: The Ansible module to fetch username, password and switch.
    :return: The cli string for further processing.
    """
    username = module.params['pn_cliusername']
    password = module.params['pn_clipassword']

    if username and password:
        cli = '/usr/bin/cli --quiet --user %s:%s' % (username, password)
    else:
        cli = '/usr/bin/cli --quiet '

    return cli


def run_cli(module, cli, find_str, out_msg):
    """
    This method executes the cli command on the target node(s) and returns the
    output.
    :param module: The Ansible module to fetch input parameters.
    :param cli: the complete cli string to be executed on the target node(s).
    :param find_str: String to search/find in output string.
    :param out_msg: Output string describing command output.
    :return: Output/Error message depending upon the response from cli.
    """
    cli = shlex.split(cli)
    rc, out, err = module.run_command(cli)

    if out:
        if out.find(find_str) > -1:
            return '%s: Successful' % out_msg
    else:
        module.exit_json(
            failed=True,
            changed=False,
            stderr=err.strip(),
            msg='%s: Failed' % out_msg
        )


def test_fabric_creation(module):
    """
    Test whether fabric got created or switch is a part of the fabric.
    :param module: The Ansible module to fetch input parameters.
    :return: Output of run_cli() method.
    """
    switch_count = module.params['pn_switch_count']
    find_str = 'Count: ' + switch_count
    cli = pn_cli(module)
    cli += ' fabric-node-show count-output '
    return run_cli(module, cli, find_str, 'Fabric create/join')


def test_fabric_control_network(module):
    """
    Test if fabric control network is management.
    :param module: The Ansible module to fetch input parameters.
    :return: Output of run_cli() method.
    """
    cli = pn_cli(module)
    cli += ' fabric-info format control-network '
    return run_cli(module, cli, 'mgmt', 'Configure fabric control network')


def test_cluster_creation(module):
    """
    Test cluster creation.
    :param module: The Ansible module to fetch input parameters.
    :return: Output of run_cli() method.
    """
    cli = pn_cli(module)
    cli += ' cluster-show count-output '
    return run_cli(module, cli, 'Count:', 'Cluster creation')


def test_vrouter_creation(module):
    """
    Test vrouters creation.
    :param module: The Ansible module to fetch input parameters.
    :return: Output of run_cli() method.
    """
    cli = pn_cli(module)
    cli += ' vrouter-show count-output '
    return run_cli(module, cli, 'Count:', 'Vrouters creation')


def test_vrouter_interface_creation(module):
    """
    Test vrouters interface creation.
    :param module: The Ansible module to fetch input parameters.
    :return: Output of run_cli() method.
    """
    cli = pn_cli(module)
    cli += ' vrouter-interface-show count-output '
    return run_cli(module, cli, 'Count:', 'Vrouter interfaces creation')


def main():
    """ This section is for arguments parsing """
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=False, type='str'),
            pn_clipassword=dict(required=False, type='str', no_log=True),
            pn_switch_count=dict(required=False, type='str'),
        )
    )

    msg = ' '
    msg += test_fabric_creation(module)
    msg += '\n'
    msg += test_fabric_control_network(module)
    msg += '\n'
    msg += test_cluster_creation(module)
    msg += '\n'
    msg += test_vrouter_creation(module)
    msg += '\n'
    msg += test_vrouter_interface_creation(module)

    module.exit_json(
        msg=msg,
        changed=False,
    )


# AnsibleModule boilerplate
from ansible.module_utils.basic import AnsibleModule

if __name__ == '__main__':
    main()

