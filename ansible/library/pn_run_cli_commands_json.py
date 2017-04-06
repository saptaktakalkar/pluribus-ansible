#!/usr/bin/python
""" PN CLI COMMANDS EXECUTION"""

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
import re

DOCUMENTATION = """
---
module: pn_run_cli_commands
author: "Pluribus Networks (devops@pluribusnetworks.com)"
version: 1
short_description: Module to execute commands from a csv file.
description:
     This module allows user to run a set of additional commands from a file.
     It performs following step:
         - Executing file commands
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
    pn_commands_file:
      description:
        - Specify commands to be run on the switches.
        required: True
        type: str
"""

EXAMPLES = """
    - name: Run Cli commands
      pn_run_cli_commands:
        pn_cliusername: "{{ USERNAME }}"
        pn_clipassword: "{{ PASSWORD }}"
        pn_commands_file: "{{ lookup('file', '{{ csv_file }}') }}"
"""

RETURN = """
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
    :param module: The Ansible module to fetch username, password and switch
    :return: The cli string for further processing
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
    Method to execute the cli command on the target node(s) and returns the
    output.
    :param module: The Ansible module to fetch input parameters.
    :param cli: The complete cli string to be executed on the target node(s).
    :return: Output/Error or Success msg depending upon the response from cli.
    """
    cli = shlex.split(cli)
    rc, out, err = module.run_command(cli)
    results = []
    if out:
        return out

    if err:
        json_msg = {'switch': '', 'output': u'Operation Failed: {}'.format(str(cli))}
        results.append(json_msg)
        module.exit_json(
            unreachable=False,
            failed=True,
            exception='',
            summary=results,
            task='Module to execute commands from a file',
            stderr=err.strip(),
            msg='Commands execution from file failed',
            changed=False
        )
    else:
        return 'Success'


def execute_commands(module, commands_data):
    """
    This method executes the cli commands from a local file.
    :param module: The Ansible module to fetch input parameters.
    :param commands_data: Cli commands in the form of string.
    :return: Output/Error or Success message depending upon the response.
    """
    output = ''
    commands_list = commands_data.split('\n')
    line_count = 0
    cli = pn_cli(module)
    clicopy = cli

    while line_count < len(commands_list):
        if commands_list[line_count] == "":
            line_count += 1

        # Execute commands from [ALL] group.
        # It will be executed on all switches.
        elif re.match("(^\[ALL.*)", commands_list[line_count]) is not None:
            line_count += 1
            cli = clicopy
            cli += " fabric-node-show format name no-show-headers "
            switch_list = run_cli(module, cli).split()

            while (line_count < len(commands_list) and
                           re.match("(^\[switch.*)",
                                    commands_list[line_count]) is None and
                           re.match("(^\[fabric.*)",
                                    commands_list[line_count]) is None):
                if commands_list[line_count] != "":
                    command = commands_list[line_count]
                    for switch in switch_list:
                        cli = clicopy
                        cli += ' switch %s ' % switch
                        cli += str(command)
                        return_msg = run_cli(module, cli)
                        output += switch + ': ' + cli + ' executed '
                        output += 'with message %s \n' % return_msg

                line_count += 1

        # Execute commands from [fabric] group.
        # It will be executed fabric wide on first switch from hosts file.
        elif re.match("(^\[fabric.*)", commands_list[line_count]) is not None:
            line_count += 1
            while (line_count < len(commands_list) and
                           re.match("(^\[switch.*)",
                                    commands_list[line_count]) is None and
                           re.match("(^\[ALL.*)",
                                    commands_list[line_count]) is None):
                if commands_list[line_count] != "":
                    command = commands_list[line_count]
                    cli = clicopy
                    cli += str(command)
                    return_msg = run_cli(module, cli)
                    output += 'fabric_wide' + ': ' + cli + ' executed '
                    output += 'with message %s \n' % return_msg
                line_count += 1

        # Execute commands from [switch] group.
        # It will be executed on mentioned switches.
        elif re.match("(^\[switch.*)", commands_list[line_count]) is not None:
            switch_to_run = commands_list[line_count].split(",")
            switch_to_run[0] = switch_to_run[0].split(" ")[1]
            last_arg = len(switch_to_run) - 1
            switch_to_run[last_arg] = switch_to_run[last_arg].split("]")[0]
            line_count += 1

            while (line_count < len(commands_list) and
                           re.match("(^\[ALL.*)",
                                    commands_list[line_count]) is None and
                           re.match("(^\[switch.*)",
                                    commands_list[line_count]) is None and
                           re.match("(^\[fabric.*)",
                                    commands_list[line_count]) is None):
                if commands_list[line_count] != "":
                    command = commands_list[line_count]
                    for switch in switch_to_run:
                        switch = switch.replace(" ", "")
                        cli = clicopy
                        cli += ' switch %s ' % switch
                        cli += str(command)
                        return_msg = run_cli(module, cli)
                        output += switch + ': ' + cli + ' executed '
                        output += 'with message %s \n' % return_msg
                line_count += 1

        # It will take care of comments at the top if any
        else:
            line_count += 1

    return output


def main():
    """ This section is for arguments parsing """
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=False, type='str'),
            pn_clipassword=dict(required=False, type='str', no_log=True),
            pn_commands_file=dict(required=True, type='str'),
        )
    )

    message = execute_commands(module, module.params['pn_commands_file'])

    message_string = message
    results = []

    for line in message_string.splitlines():
        if ': ' in line:
            return_msg = line.split(': ')
            json_msg = {'switch' : return_msg[0] , 'output' : return_msg[1].strip() }
            results.append(json_msg)

    module.exit_json(
        unreachable=False,
        summary=results,
        exception='',
        msg = 'Commands execution from file executed successfully',
        failed=False,
        changed=True,
        task='Module to execute commands from file'
    )


# AnsibleModule boilerplate
from ansible.module_utils.basic import AnsibleModule

if __name__ == '__main__':
    main()

