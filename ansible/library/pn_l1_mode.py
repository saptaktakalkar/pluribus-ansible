#!/usr/bin/python
""" PN CLI L1 Switch Mode """

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
import time

DOCUMENTATION = """
---
module: pn_l1_mode
author: "Pluribus Networks (@saptaktakalkar)"
version: 1
short_description: CLI command to configure L1 switch mode.
description:
    L1 switch mode allows you to create port associations between two
    hosts/switches which are not connected to each other. It creates a
    virtual wire between them so that traffic can flow between those.
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
    pn_l1_switch:
      description:
        - Name of the switch to be put in L1 mode.
      required: True
      type: str
    pn_end_switch1:
      description:
        - Name of the end point switch.
      required: True
      type: str
    pn_end_switch2:
      description:
        - Name of the other end point switch.
      required: True
      type: str
    pn_port_assn_name:
      description:
        - Port association name to be assigned.
      required: False
      type: str
      default: None
    pn_bi_directional:
      description:
        - Port association flag.
      required: False
      type: bool
      default: True
"""

EXAMPLES = """
    - name: Configure L1 switch mode
      pn_l1_mode:
        pn_l1_switch: 'auto-spine2'
        pn_end_switch1: 'auto-leaf3'
        pn_end_switch2: 'auto-leaf4'
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


def run_cli(module, cli):
    """
    This method executes the cli command on the target node(s) and returns the
    output.
    :param module: The Ansible module to fetch input parameters.
    :param cli: the complete cli string to be executed on the target node(s).
    :return: Output/Error or Success message depending upon
    the response from cli.
    """
    cli = shlex.split(cli)
    rc, out, err = module.run_command(cli)

    if out:
        return out

    if err:
        module.exit_json(
            error="1",
            failed=True,
            stderr=err.strip(),
            msg="Operation Failed: " + str(cli),
            changed=False
        )
    else:
        return 'Success'


def modify_switch_mode_to_l1(module, l1_switch):
    """
    Method to put the switch in L1 mode i.e. virtual-wire
    :param module: The Ansible module to fetch input parameters.
    :param l1_switch: Name of the L1 switch.
    :return: Output of 'switch-mode-show' command.
    """
    cli = pn_cli(module)
    cli += ' --no-login-prompt '
    # cli += ' switch ' + l1_switch
    cli += ' switch-mode-modify switch-mode virtual-wire '

    run_cli(module, cli)
    time.sleep(10)   # Wait for nvOS to restart

    cli = pn_cli(module)
    cli += ' switch-mode-show '
    return run_cli(module, cli)


def get_ports(module, l1_switch, end_switch):
    """
    Method to get list of ports on L1 switch connected to end switch.
    :param module: The Ansible module to fetch input parameters.
    :param l1_switch: Name of the L1 switch.
    :param end_switch: Name of the end switch connected to L1 switch.
    :return: List of ports.
    """
    cli = pn_cli(module)
    # cli += ' switch ' + l1_switch
    cli += ' lldp-show format local-port no-show-headers '
    ports = run_cli(module, cli).split()

    cli = pn_cli(module)
    # cli += ' switch ' + l1_switch
    cli += ' lldp-show format sys-name no-show-headers '
    sys_names = run_cli(module, cli).split()

    port_list = []
    for index, system in enumerate(sys_names):
        if system in end_switch:
            port_list.append(ports[index])

    return port_list


def create_port_association(module, l1_switch, port_assn_name,
                            master_ports, slave_ports):
    """
    Method to create port association on L1 switch.
    :param module: The Ansible module to fetch input parameters.
    :param l1_switch: Name of L1 switch.
    :param port_assn_name: Name to be assigned to port association.
    :param master_ports: List of master ports.
    :param slave_ports: List of slave ports.
    :return:
    """
    bi_directional = module.params['pn_bi_directional']
    association = 'bidir' if bi_directional else 'no-bidir'

    cli = pn_cli(module)
    # cli += ' switch ' + l1_switch
    cli += ' port-association-create name ' + port_assn_name
    # One to many port association (1 master port, many slave ports)
    cli += ' master-ports ' + str(master_ports[0])
    cli += ' slave-ports ' + ','.join(slave_ports)
    cli += ' virtual-wire ' + association
    run_cli(module, cli)

    cli = pn_cli(module)
    # cli += ' switch ' + l1_switch
    cli += ' port-association-show '
    return run_cli(module, cli)


def main():
    """ This section is for arguments parsing """

    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=False, type='str'),
            pn_clipassword=dict(required=False, type='str', no_log=True),
            pn_l1_switch=dict(required=True, type='str'),
            pn_end_switch1=dict(required=True, type='str'),
            pn_end_switch2=dict(required=True, type='str'),
            pn_port_assn_name=dict(required=False, type='str', default=None),
            pn_bi_directional=dict(required=False, type='bool', default='True')
        )
    )

    l1_switch = module.params['pn_l1_switch']
    end_switch1 = module.params['pn_end_switch1']
    end_switch2 = module.params['pn_end_switch2']
    port_assn_name = module.params['pn_port_assn_name']
    if port_assn_name is None:
        port_assn_name = end_switch1 + '-assn-' + end_switch2

    # Get the list of master ports
    master_ports = get_ports(module, l1_switch, end_switch1)
    message = ' List of master ports: ' + ','.join(master_ports) + '\n'

    # Get the list of slave ports
    slave_ports = get_ports(module, l1_switch, end_switch2)
    message += ' List of slave ports: ' + ','.join(slave_ports) + '\n'

    # Put switch in L1 mode
    message += modify_switch_mode_to_l1(module, l1_switch)
    message += ' %s switch is in L1 mode now ' % l1_switch + '\n'

    # Create port association
    message += create_port_association(module, l1_switch, port_assn_name,
                                       master_ports, slave_ports)

    module.exit_json(
        stdout=message,
        error="0",
        failed=False,
        msg="Operation Completed",
        changed=True
    )

# AnsibleModule boilerplate
from ansible.module_utils.basic import AnsibleModule

if __name__ == '__main__':
    main()

