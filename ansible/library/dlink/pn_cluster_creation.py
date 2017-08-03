#!/usr/bin/python
""" PN Cluster Creation """

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

from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = """
---
module: pn_cluster_creation
author: 'Pluribus Networks (devops@pluribusnetworks.com)'
description: Module to create cluster.
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
    pn_switch_list:
      description:
        - Specify list of all switches.
      required: False
      type: list
      default: []
"""

EXAMPLES = """
- name: Create cluster
  pn_cluster_creation:
    pn_cliusername: "{{ USERNAME }}"
    pn_clipassword: "{{ PASSWORD }}"
    pn_switch_list: "{{ groups['switch'] }}"
"""

RETURN = """
summary:
  description: It contains output of each configuration along with switch name.
  returned: always
  type: str
changed:
  description: Indicates whether the CLI caused changes on the target.
  returned: always
  type: bool
unreachable:
  description: Indicates whether switch was unreachable to connect.
  returned: always
  type: bool
failed:
  description: Indicates whether or not the execution failed on the target.
  returned: always
  type: bool
exception:
  description: Describes error/exception occurred while executing CLI command.
  returned: always
  type: str
task:
  description: Name of the task getting executed on switch.
  returned: always
  type: str
msg:
  description: Indicates whether configuration made was successful or failed.
  returned: always
  type: str
"""

CHANGED_FLAG = []


def pn_cli(module):
    """
    Generate the cli portion to launch the Netvisor cli.
    :param module: The Ansible module to fetch username and password.
    :return: The cli string for further processing.
    """
    username = module.params['pn_cliusername']
    password = module.params['pn_clipassword']

    if username and password:
        cli = '/usr/bin/cli --quiet --user %s:%s ' % (username, password)
    else:
        cli = '/usr/bin/cli --quiet '

    return cli


def run_cli(module, cli):
    """
    Execute the cli command on the target node(s) and returns the output.
    :param module: The Ansible module to fetch input parameters.
    :param cli: The complete cli string to be executed on the target node(s).
    :return: Output or Error msg depending upon the response from cli else None.
    """
    results = []
    cli = shlex.split(cli)
    rc, out, err = module.run_command(cli)

    if out:
        return out
    if err:
        json_msg = {
            'switch': module.params['pn_switch_list'][0],
            'output': u'Operation Failed: {}'.format(' '.join(cli))
        }
        results.append(json_msg)
        module.exit_json(
            unreachable=False,
            failed=True,
            exception=err.strip(),
            summary=results,
            task='Create cluster',
            msg='Cluster creation failed',
            changed=False
        )
    else:
        return None


def create_cluster(module, switch_list):
    """
    Create a cluster between two switches.
    :param module: The Ansible module to fetch input parameters.
    :param switch_list: List of switches.
    :return: String describing if cluster got created or not.
    """
    global CHANGED_FLAG
    output = ''
    new_cluster = False

    node1 = switch_list[0]
    node2 = switch_list[1]

    name = node1 + '-' + node2 + '-cluster'

    cli = pn_cli(module)
    cli += ' switch %s cluster-show format name no-show-headers ' % node1
    cluster_list = run_cli(module, cli)

    if cluster_list is not None:
        cluster_list = cluster_list.split()
        if name not in cluster_list:
            new_cluster = True

    if new_cluster or cluster_list is None:
        cli = pn_cli(module)
        cli += ' switch %s cluster-create name %s ' % (node1, name)
        cli += ' cluster-node-1 %s cluster-node-2 %s ' % (node1, node2)
        run_cli(module, cli)
        CHANGED_FLAG.append(True)
        output += '%s: Created cluster %s\n' % (node1, name)

    return output


def main():
    """ This section is for arguments parsing """
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=False, type='str'),
            pn_clipassword=dict(required=False, type='str', no_log=True),
            pn_switch_list=dict(required=False, type='list', default=[]),
        )
    )

    global CHANGED_FLAG
    results = []
    message = ''
    switch_list = module.params['pn_switch_list']

    # Create cluster
    if len(switch_list) == 2:
        message += create_cluster(module, switch_list)

    for switch in switch_list:
        replace_string = switch + ': '
        for line in message.splitlines():
            if replace_string in line:
                results.append({
                    'switch': switch,
                    'output': (line.replace(replace_string, '')).strip()
                })

    # Exit the module and return the required JSON.
    module.exit_json(
        unreachable=False,
        msg='cluster creation succeeded',
        summary=results,
        exception='',
        failed=False,
        changed=True if True in CHANGED_FLAG else False,
        task='Create clusters'
    )

if __name__ == '__main__':
    main()

