#!/usr/bin/python
""" Tests for L2 VRRP """

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
module: pn_test_l2_vrrp
author: "Pluribus Networks (devops@pluribusnetworks.com)"
short_description: Tests for L2 VRRP.
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
    pn_spine_count:
      description:
        - Number of spine switches.
      required: False
      type: int
    pn_leaf_count:
      description:
        - Number of leaf switches.
      required: False
      type: int
"""

EXAMPLES = """
- name: Test Layer2 VRRP
  pn_test_l2_vrrp:
  pn_cliusername: "{{ USERNAME }}"
  pn_clipassword: "{{ PASSWORD }}"
  pn_spine_count: "{{ spine_count }}"
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


def test_vlan_creation(module, vlan_list):
    """
    Test vlan creation.
    :param module: The Ansible module to fetch input parameters.
    :param vlan_list: List of vlan ids to test.
    :return: Output of run_cli() method.
    """
    if vlan_list:
        output = ''
        switch_count = module.params['pn_spine_count'] + module.params[
            'pn_leaf_count']
        find_str = 'Count: ' + str(switch_count)
        for vlan_id in vlan_list:
            cli = pn_cli(module)
            cli += ' vlan-show id %s count-output ' % vlan_id
            out_msg = 'Vlan %s creation' % vlan_id
            output += run_cli(module, cli, find_str, out_msg)

        return output
    else:
        return 'Vlan creation: Failed\n'


def test_vrouter_creation(module):
    """
    Test vrouters creation.
    :param module: The Ansible module to fetch input parameters.
    :return: Output of run_cli() method.
    """
    find_str = 'Count: ' + str(module.params['pn_spine_count'])
    cli = pn_cli(module)
    cli += ' vrouter-show count-output '
    return run_cli(module, cli, find_str, 'Spine vrouters creation')


def test_vrouter_interface_creation(module, interfaces_count):
    """
    Test vrouters interface creation.
    :param module: The Ansible module to fetch input parameters.
    :param interfaces_count: Count of vrouter interfaces fetched from csv file.
    :return: Output of run_cli() method.
    """
    find_str = 'Count: ' + str(interfaces_count * 4)
    cli = pn_cli(module)
    cli += ' vrouter-interface-show count-output '
    return run_cli(module, cli, find_str, 'Vrouter interfaces creation')


def main():
    """ This section is for arguments parsing """
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=False, type='str'),
            pn_clipassword=dict(required=False, type='str', no_log=True),
            pn_spine_count=dict(required=False, type='int'),
            pn_leaf_count=dict(required=False, type='int'),
            pn_csv_data=dict(required=True, type='str'),
        )
    )

    vlan_list = []
    csv_data_row_count = 0
    csv_data = module.params['pn_csv_data'].replace(" ", "")
    csv_data_list = csv_data.split('\n')
    for row in csv_data_list:
        elements = row.split(',')
        vlan_list.append(elements[1])
        csv_data_row_count += 1

    msg = test_vlan_creation(module, vlan_list)
    msg += test_vrouter_creation(module)
    msg += test_vrouter_interface_creation(module, csv_data_row_count)

    module.exit_json(
        stdout=msg,
        changed=False,
    )

if __name__ == '__main__':
    main()

