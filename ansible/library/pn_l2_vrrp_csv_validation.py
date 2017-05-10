#!/usr/bin/python
""" PN L2 VRRP CSV Validation """

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
import socket

from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = """
---
module: pn_l2_vrrp_csv_validation
author: 'Pluribus Networks (devops@pluribusnetworks.com)'
short_description: Module to validate L2 VRRP configuration csv file.
description:
    L2 VRRP config csv file format: IP, VLAN ID, SWITCH NAME
    Every row in the csv file should have above 3 elements.
    Csv file should not be empty. This module validates the given csv file.
options:
    pn_csv_data:
      description: String containing L2 VRRP data parsed from csv file.
      required: True
      type: str
    pn_leaf_list:
      description: Specify list of spine switches.
      required: True
      type: list
"""

EXAMPLES = """
- name: Validate L2 VRRP csv file
  pn_l2_vrrp_csv_validation:
    pn_csv_data: "{{ lookup('file', '{{ csv_file }}') }}"
    pn_spine_list: "{{ groups['spine'] }}"
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
            pn_csv_data=dict(required=True, type='str'),
            pn_spine_list=dict(required=False, type='list'),
        )
    )

    output = ''
    line_count = 0
    switch_vlan_dict = {}
    csv_data = module.params['pn_csv_data'].replace(' ', '')

    if csv_data:
        csv_data_list = csv_data.split('\n')
        for row in csv_data_list:
            row = row.strip()
            line_count += 1
            valid_vlan = False
            valid_switch = False
            if row.startswith('#'):
                # Skip comments which starts with '#'
                continue
            else:
                elements = row.split(',')
                # Check number of elements per row. Should be 3 for L2 VRRP.
                if len(elements) != 3:
                    output += 'Invalid number of elements '
                    output += 'at line number {}. '.format(line_count)
                    output += 'It should have 3 elements (IP, Vlan, Switch)\n'
                else:
                    ip = elements[0]
                    vlan = elements[1]
                    switch = elements[2]

                    if not ip or not vlan or not switch:
                        output += 'Invalid entry at line number {}\n'.format(
                            line_count
                        )
                    else:
                        # IP address validation
                        try:
                            if '/' not in ip:
                                raise socket.error
                            else:
                                address_with_subnet = ip.split('/')
                                address = address_with_subnet[0]
                                subnet = address_with_subnet[1]
                                dot_count = address.count('.')
                                if dot_count != 3:
                                    raise socket.error

                                socket.inet_aton(address)
                                if (not subnet.isdigit() or
                                        int(subnet) not in range(1, 33)):
                                    raise socket.error
                        except socket.error:
                            output += 'Invalid IP {} '.format(ip)
                            output += 'at line number {}\n'.format(line_count)

                        # Vlan ID validation
                        if (not vlan.isdigit() or
                                int(vlan) not in range(2, 4093)):
                            output += 'Invalid VLAN ID {} '.format(vlan)
                            output += 'at line number {}\n'.format(line_count)
                        else:
                            valid_vlan = True

                        # Switch name validation
                        if (re.match("^[a-zA-Z0-9_.:-]+$", switch) is None or
                                switch not in module.params['pn_spine_list']):
                            output += 'Invalid SWITCH NAME {} '.format(switch)
                            output += 'at line number {}\n'.format(line_count)
                        else:
                            valid_switch = True
                            if switch not in switch_vlan_dict:
                                switch_vlan_dict[switch] = []

                        # Check for duplicate vlans.
                        # A router can have only 1 interface per vlan.
                        if valid_vlan and valid_switch:
                            vlans_list = switch_vlan_dict[switch]
                            if vlan not in vlans_list:
                                vlans_list.append(vlan)
                                switch_vlan_dict[switch] = vlans_list
                            else:
                                output += 'Duplicate vlan entry at '
                                output += 'line number {}. '.format(line_count)
                                output += 'A router can have only one '
                                output += 'interface per vlan\n'
    else:
        output += 'Csv file should not be empty\n'

    if not output:
        msg = 'Valid csv file'
        failed_flag = False
    else:
        msg = 'Invalid csv file'
        failed_flag = True

    module.exit_json(
        unreachable=False,
        msg=output,
        summary=msg,
        exception='',
        failed=failed_flag,
        changed=False,
        task='Validate L2 VRRP csv file'
    )


if __name__ == '__main__':
    main()

