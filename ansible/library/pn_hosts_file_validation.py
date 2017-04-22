#!/usr/bin/python
""" PN HOSTS FILE Validation """

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

import re

from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = """
---
module: pn_hosts_file_validation
author: 'Pluribus Networks (devops@pluribusnetworks.com)'
short_description: Module to validate L2 VRRP configuration csv file.
description:
    HOSTS file format: switch_name ansible_hosts=ip_address
    Every row in the hosts file should have above 2 elements.
    Hosts file should not be empty. This module validates the given hosts file.
options:
    pn_hosts_file_data:
      description: String containing Hosts file data parsed from ini file.
      required: True
      type: str
"""

EXAMPLES = """
- name: Validate HOSTS file
  pn_hosts_file_validation:
    pn_hosts_file_data: "{{ lookup('file', '{{ ini_file }}') }}"
"""

RETURN = """
msg:
  description: It contains output of each validation.
  returned: always
  type: str
changed:
  description: Indicates whether the validation caused changes on the target.
  returned: always
  type: bool
unreachable:
  description: Empty string.
  returned: always
  type: bool
failed:
  description: Indicates if csv validation failed or not.
  returned: always
  type: bool
exception:
  description: Empty string.
  returned: always
  type: str
task:
  description: Name of the task getting executed.
  returned: always
  type: str
summary:
  description: Indicates whether csv file is valid or invalid.
  returned: always
  type: str
"""


def main():
    """ This section is for arguments parsing """
    module = AnsibleModule(
        argument_spec=dict(
            pn_hosts_file_data=dict(required=True, type='str'),
        )
    )

    host_names = []
    ip_list = []
    output = ''
    hosts_file_data = module.params['pn_hosts_file_data'].replace(' ', '')

    if hosts_file_data:
        input = hosts_file_data.split('\n')
        if '[leaf]' not in input:
            output += 'No leaf section in the hosts file \n'
        elif '[spine]' not in input:
            output += 'No spine section in the hosts file \n'
        else:
            line_count = 0
            while line_count < len(input):
                if input[line_count] == "":
                    line_count += 1

                elif re.match("(^\#.*)", input[line_count]) is not None:
                    line_count += 1

                elif re.match("(^\[.*)", input[line_count]) is not None:
                    line_count += 1

                else:
                    host_line = input[line_count].split()
                    if len(host_line) != 2:
                        output += 'Invalid number of elements '
                        output += 'at line number {0}. '.format(line_count + 1)
                        output += 'It should have 2 elements (switch_name, ansible_host=ip_address)\n'
                    else:
                        if host_line[0] in host_names:
                            output += 'Duplicate host name '
                            output += 'at line number {0}\n'.format(line_count + 1)
                        else:
                            ip = host_line[1].split('=')
                            if ip[0] != 'ansible_host':
                                output += 'The spelling error in ansible_host keyword '
                                output += 'at line number {0}.\n'.format(line_count + 1)
                            else:

                                if len(ip) == 2:
                                    ip = ip[1]

                                    if re.match("(^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$)", ip) is not None:
                                        if ip in ip_list:
                                            output += 'Duplicate ip address '
                                            output += 'at line number {0}\n'.format(line_count + 1)
                                        else:
                                            host_names.append(host_line[0])
                                            ip_list.append(ip)
                                    else:
                                        output += 'Invalid IP {0} '.format(ip)
                                        output += 'at line number {0}\n'.format(line_count + 1)

                                else:
                                    output += 'ip address missing in 2nd column'
                                    output += 'at line number {0}\n'.format(line_count + 1)

                    line_count += 1
            if len(ip_list) < 1:
                output += 'The count of valid hosts is less than 1\n'

    else:
        output += 'Hosts file should not be empty\n'

    if not output:
        msg = 'Valid hosts file'
        failed_flag = False
    else:
        msg = 'Invalid hosts file'
        failed_flag = True

    module.exit_json(
        unreachable=False,
        msg=output,
        summary=msg,
        exception='',
        failed=failed_flag,
        changed=False,
        task='Validate hosts file'
    )


if __name__ == '__main__':
    main()
