#!/usr/bin/python
""" Tests for L2 ZTP with 3rd party switches """

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
module: pn_test_l2_ztp_third_party
author: "Pluribus Networks (devops@pluribusnetworks.com)"
short_description: Tests for L2 ZTP with third party switches.
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
    pn_leaf_count:
      description:
        - Number of leaf switches.
      required: False
      type: int
"""

EXAMPLES = """
- name: Test Layer2 Zero Touch Provisioning with 3rd party switches
  pn_test_l2_ztp_third_party:
  pn_cliusername: "{{ USERNAME }}"
  pn_clipassword: "{{ PASSWORD }}"
  pn_leaf_count: "{{ leaf_count }}"
"""

RETURN = """
stdout:
  description: The set of responses for each command.
  returned: always
  type: str
changed:
  description: Indicates whether the CLI caused changes on the target.
  returned: always
  type: bool
failed:
  description: Indicates whether or not the execution failed on the target.
  returned: always
  type: bool
"""


def pn_cli(module):
    """
    Method to generate the cli portion to launch the Netvisor cli.
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
    Method to execute the cli command on the target node(s) and returns the
    output.
    :param module: The Ansible module to fetch input parameters.
    :param cli: the complete cli string to be executed on the target node(s).
    :param find_str: String to search/find in output string.
    :param out_msg: Output string describing command output.
    :return: Success/Fail message depending upon the response from cli.
    """
    cli = shlex.split(cli)
    rc, out, err = module.run_command(cli)

    if out:
        if out.find(find_str) > -1:
            return '%s: Successful\n' % out_msg

    return '%s: Failed\n' % out_msg


def test_fabric_creation(module):
    """
    Test whether fabric got created or switch is a part of the fabric.
    :param module: The Ansible module to fetch input parameters.
    :return: Output of run_cli() method.
    """
    switch_count = module.params['pn_leaf_count']
    find_str = 'Count: ' + str(switch_count)
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


def test_trunk_creation(module):
    """
    Test trunk creation.
    :param module: The Ansible module to fetch input parameters.
    :return: Output of run_cli() method.
    """
    cli = pn_cli(module)
    cli += ' trunk-show count-output '
    return run_cli(module, cli, 'Count:', 'Trunk creation')


def test_vlag_creation(module):
    """
    Test vlags creation.
    :param module: The Ansible module to fetch input parameters.
    :return: Output of run_cli() method.
    """
    cli = pn_cli(module)
    cli += ' vlag-show count-output '
    return run_cli(module, cli, 'Count:', 'vLags creation')


def main():
    """ This section is for arguments parsing """
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=False, type='str'),
            pn_clipassword=dict(required=False, type='str', no_log=True),
            pn_leaf_count=dict(required=False, type='int'),
        )
    )

    msg = test_fabric_creation(module)
    msg += test_fabric_control_network(module)
    msg += test_cluster_creation(module)
    msg += test_trunk_creation(module)
    msg += test_vlag_creation(module)

    module.exit_json(
        stdout=msg,
        changed=False,
    )

if __name__ == '__main__':
    main()

