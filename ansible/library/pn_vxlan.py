#!/usr/bin/python
""" PN CLI VXLAN """

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
module: pn_vxlan
author: 'Pluribus Networks (@saptaktakalkar)'
version: 1
short_description: CLI command to configure/add vxlan.
description: VXLAN is network virtualization technology that attempts to
improve the scalability problems associated with large cloud computing
deployments.
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
    pn_spine_list:
      description:
        - Specify list of Spine hosts
      required: False
      type: list
    pn_leaf_list:
      description:
        - Specify list of leaf hosts
      required: False
      type: list
    pn_csv_data:
      description:
        - String containing vrrp data parsed from csv file.
      required: False
      type: str
"""

EXAMPLES = """
    - name: Add vxlan
      pn_vxlan:
        pn_cliusername: "{{ USERNAME }}"
        pn_clipassword: "{{ PASSWORD }}"
        pn_spine_list: "{{ groups['spine'] }}"
        pn_leaf_list: "{{ groups['leaf'] }}"
        pn_csv_data: "{{ lookup('file', '{{ csv_file }}') }}"
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


CHANGED_FLAG = []


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
    This method executes the cli command on the target node(s) and returns the
    output.
    :param module: The Ansible module to fetch input parameters.
    :param cli: the complete cli string to be executed on the target node(s).
    :return: Output/Error or Success message depending upon.
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


def create_vlan_with_vxlan_mapping(module, vlan_id, vxlan):
    """
    Method to create vlan with vxlan mapping.
    :param module: The Ansible module to fetch input parameters.
    :param vlan_id: vlan id to be created.
    :param vxlan: vxlan id to be assigned to vlan.
    :return: String describing if vlan got created or if it already exists.
    """
    global CHANGED_FLAG
    output = ''
    cli = pn_cli(module)
    clicopy = cli
    cli += ' vlan-show format id no-show-headers '
    existing_vlan_ids = run_cli(module, cli).split()
    existing_vlan_ids = list(set(existing_vlan_ids))

    if vlan_id not in existing_vlan_ids:
        cli = clicopy
        cli += ' vlan-create id ' + vlan_id
        cli += ' vxlan ' + vxlan
        cli += ' scope fabric '
        run_cli(module, cli)
        output += ' vlan with id ' + vlan_id + ' created! '
        CHANGED_FLAG.append(True)
    else:
        output += ' vlan with id ' + vlan_id + ' already exists! '
        CHANGED_FLAG.append(False)

    return output


def create_tunnel(module, tunnel_name, local_ip, remote_ip, vrouter_name):
    """
    Method to create tunnel to carry vxlan traffic.
    :param module: The Ansible module to fetch input parameters.
    :param tunnel_name: Name of the tunnel to create.
    :param local_ip: Local vrouter interface ip.
    :param remote_ip: Remote vrouter interface ip.
    :param vrouter_name: Name of the vrouter.
    :return: String describing if tunnel got created or if it already exists.
    """
    global CHANGED_FLAG
    cli = pn_cli(module)
    cli += ' tunnel-show format name no-show-headers '
    existing_tunnels = run_cli(module, cli).split()

    if tunnel_name not in existing_tunnels:
        cli = pn_cli(module)
        cli += ' tunnel-create name %s scope local ' % tunnel_name
        cli += ' local-ip %s remote-ip %s vrouter-name %s ' % (local_ip,
                                                               remote_ip,
                                                               vrouter_name)
        if 'Success' in run_cli(module, cli):
            CHANGED_FLAG.append(True)
            return ' %s on %s created successfully! ' % (tunnel_name,
                                                         vrouter_name)
        else:
            CHANGED_FLAG.append(False)
            return ' Could not create %s! ' % tunnel_name
    else:
        CHANGED_FLAG.append(False)
        return ' %s on %s already exists! ' % (tunnel_name, vrouter_name)


def find_vrouter_interface_ip(module, local_switch, vrouter_name,
                              remote_switch):
    """
    Method to find vrouter interface ip on a vrouter needed for tunnel creation.
    :param module: The Ansible module to fetch input parameters.
    :param local_switch: Name of the local switch.
    :param vrouter_name: Name of the vrouter on that local switch.
    :param remote_switch: Name of the remote switch.
    :return: Required vrouter interface ip.
    """
    cli = pn_cli(module)
    clicopy = cli
    cli += ' vrouter-interface-show vrouter-name %s ' % vrouter_name
    cli += ' format l3-port no-show-headers '
    port_numbers = run_cli(module, cli).split()
    port_numbers = list(set(port_numbers))
    port_numbers.remove(vrouter_name)

    for port in port_numbers:
        cli = clicopy
        cli += ' switch %s port-show port %s ' % (local_switch, port)
        cli += ' format hostname no-show-headers '
        hostname = run_cli(module, cli).split()[0]
        if hostname in remote_switch:
            cli = clicopy
            cli += ' vrouter-interface-show vrouter-name %s ' % vrouter_name
            cli += ' l3-port %s format ip no-show-headers ' % port
            ip_with_subnet = run_cli(module, cli).split()
            ip_with_subnet.remove(vrouter_name)
            ip_with_subnet = ip_with_subnet[0].split('/')
            return ip_with_subnet[0]


def get_vrouter_name(module, switch_name):
    """
    Method to return name of the vrouter.
    :param module: The Ansible module to fetch input parameters.
    :param switch_name: Name of the switch for which to find the vrouter.
    :return: Vrouter name.
    """
    cli = pn_cli(module)
    cli += ' vrouter-show location ' + switch_name
    cli += ' format name no-show-headers '
    return run_cli(module, cli).split()[0]


def configure_vtep(module, local_switch, csv_data_list):
    """
    Method to configure virtual tunnel end points.
    :param module: The Ansible module to fetch input parameters.
    :param local_switch: Name of the local switch.
    :param csv_data_list: vxlan data in comma separated format.
    :return: String describing output of configuration.
    """
    spine_list = module.params['pn_spine_list']
    leaf_list = module.params['pn_leaf_list']
    local_vrouter_name = get_vrouter_name(module, local_switch)
    output = ''
    for row in csv_data_list:
        elements = row.split(',')
        if len(elements) > 6 and local_switch not in elements[2]:
            vxlan_id = elements[6]
            remote_switch = elements[2]
            remote_vrouter_name = get_vrouter_name(module, remote_switch)
            tunnel_name = local_switch + '-to-' + remote_switch + '-tunnel'

            if local_switch in spine_list or remote_switch in spine_list:
                # Leaf to Spine or Spine to Leaf
                local_ip = find_vrouter_interface_ip(module, local_switch,
                                                     local_vrouter_name,
                                                     remote_switch)
                remote_ip = find_vrouter_interface_ip(module, remote_switch,
                                                      remote_vrouter_name,
                                                      local_switch)

                output += create_tunnel(module, tunnel_name, local_ip,
                                        remote_ip, local_vrouter_name)
                output += add_vxlan_to_tunnel(module, vxlan_id, tunnel_name)
            else:
                pass    # TODO: Leaf to Leaf

    return output


def add_vxlan_to_tunnel(module, vxlan, tunnel_name):
    """
    Method to add vxlan to created tunnel so that it can carry vxlan traffic.
    :param module: The Ansible module to fetch input parameters.
    :param vxlan: vxlan id to add to tunnel.
    :param tunnel_name: Name of the tunnel on which vxlan will be added.
    :return: String describing if vxlan got added to tunnel or not.
    """
    global CHANGED_FLAG
    cli = pn_cli(module)
    cli += ' tunnel-vxlan-show format switch no-show-headers '
    existing_tunnel_vxlans = run_cli(module, cli).split()

    if tunnel_name not in existing_tunnel_vxlans:
        cli = pn_cli(module)
        cli += ' tunnel-vxlan-add name %s vxlan %s ' % (tunnel_name, vxlan)
        if 'Success' in run_cli(module, cli):
            CHANGED_FLAG.append(True)
            return ' Added vxlan %s to %s! ' % (vxlan, tunnel_name)
        else:
            CHANGED_FLAG.append(False)
            return ' Could not add vxlan %s to %s! ' % (vxlan, tunnel_name)
    else:
        CHANGED_FLAG.append(False)
        return ' vxlan %s already added to %s! ' % (vxlan, tunnel_name)


def add_ports_to_vxlan_loopback_trunk(module, ports):
    """
    Method to add ports to vxlan-loopback-trunk.
    :param module: The Ansible module to fetch input parameters.
    :param ports: Port number to add to vxlan-loopback-trunk.
    """
    cli = pn_cli(module)
    cli += ' trunk-modify name vxlan-loopback-trunk ports ' + ports
    run_cli(module, cli)


def configure_vxlan(module, csv_data):
    """
    Method to parse vxlan data from csv file and configure it.
    :param module: The Ansible module to fetch input parameters.
    :param csv_data: vxlan data in comma separated format.
    :return: String describing output of vxlan configuration.
    """
    output = ''
    csv_data = csv_data.replace(" ", "")
    csv_data_list = csv_data.split('\n')
    for row in csv_data_list:
        elements = row.split(',')
        if len(elements) > 6:
            vlan_id = elements[0]
            switch_name = elements[2]
            vxlan_id = elements[6]
            loopback_port = elements[7]
            output += create_vlan_with_vxlan_mapping(module, vlan_id, vxlan_id)
            output += configure_vtep(module, switch_name, csv_data_list)
            add_ports_to_vxlan_loopback_trunk(module, loopback_port)

    return output


def main():
    """ This section is for arguments parsing """
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=False, type='str'),
            pn_clipassword=dict(required=False, type='str', no_log=True),
            pn_spine_list=dict(required=False, type='list'),
            pn_leaf_list=dict(required=False, type='list'),
            pn_csv_data=dict(required=True, type='str'),
        )
    )

    global CHANGED_FLAG
    CHANGED_FLAG = []
    message = configure_vxlan(module, module.params['pn_csv_data'])

    module.exit_json(
        stdout=message,
        error='0',
        failed=False,
        msg='Configured VXLAN successfully.',
        changed=True if True in CHANGED_FLAG else False
    )


if __name__ == '__main__':
    main()

