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
import re
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
    :return: Output/Error or Success message depending upon
    the response from cli.
    """
    cli = shlex.split(cli)
    rc, out, err = module.run_command(cli)

    if out:
        return out

    if err:
        module.exit_json(
            error='1',
            failed=True,
            stderr=err.strip(),
            msg='Operation Failed: ' + str(cli),
            changed=False
        )
    else:
        return 'Success'


def add_vxlan_to_vlan(module, vlan_id, vxlan):
    """
    Method to add vxlan mapping to vlan.
    :param module: The Ansible module to fetch input parameters.
    :param vlan_id: vlan id to be modified.
    :param vxlan: vxlan id to be assigned to vlan.
    :return: String describing if vxlan for added or not.
    """
    cli = pn_cli(module)
    cli += ' vlan-modify id %s vxlan %s ' % (vlan_id, vxlan)
    run_cli(module, cli)
    return ' Added vxlan %s to vlan %s! ' % (vxlan, vlan_id)


def create_tunnel(module, tunnel_name, local_ip, remote_ip, vrouter_name,
                  switch):
    """
    Method to create tunnel to carry vxlan traffic.
    :param module: The Ansible module to fetch input parameters.
    :param tunnel_name: Name of the tunnel to create.
    :param local_ip: Local vrouter interface ip.
    :param remote_ip: Remote vrouter interface ip.
    :param vrouter_name: Name of the vrouter.
    :param switch: Name of the switch on which tuneel will be created.
    :return: String describing if tunnel got created or if it already exists.
    """
    global CHANGED_FLAG
    cli = pn_cli(module)
    cli += ' switch %s tunnel-show format name no-show-headers ' % switch
    existing_tunnels = run_cli(module, cli).split()

    if tunnel_name not in existing_tunnels:
        cli = pn_cli(module)
        cli += ' switch %s tunnel-create name %s scope local ' % (switch,
                                                                  tunnel_name)
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


def get_loopback_ip(module, switch):
    """
    Method to get loopback ip of a switch.
    :param module: The Ansible module to fetch input parameters.
    :param switch: Name of the switch.
    :return: Loopback ip.
    """
    vrouter_name = get_vrouter_name(module, switch)
    cli = pn_cli(module)
    cli += ' vrouter-loopback-interface-show vrouter-name ' + vrouter_name
    cli += ' format ip no-show-headers '
    return run_cli(module, cli).split()[1]


def get_vrouter_interface_ip(module, switch, vlan):
    """
    Method to get vrouter interface ip to be used as local ip.
    :param module: The Ansible module to fetch input parameters.
    :param switch: Name of the local switch.
    :param vlan: Vlan id for which to find vrouter interface ip.
    :return: Vrouter interface ip.
    """
    vrouter_name = get_vrouter_name(module, switch)
    cli = pn_cli(module)
    cli += ' vrouter-interface-show vrouter-name ' + vrouter_name
    cli += ' vlan %s format ip no-show-headers ' % vlan
    output = run_cli(module, cli).split()
    output = list(set(output))
    output.remove(vrouter_name)
    regex = re.compile(r'^\d.*1/')
    ip_with_subnet = [ip for ip in output if not regex.match(ip)]
    return ip_with_subnet[0].split('/')[0]


def configure_vtep_for_clustered_leafs(module, local_switch, vlan, vxlan):
    """
    Method to configure virtual tunnel end points for clustered leafs.
    :param module: The Ansible module to fetch input parameters.
    :param local_switch: Name of the local switch.
    :param vlan: vlan id.
    :param vxlan: Vxlan to add to tunnel.
    :return: String describing output of configuration.
    """
    non_clustered_leafs = find_non_clustered_leafs(module)
    local_ip = get_vrouter_interface_ip(module, local_switch, vlan)
    output = ''
    if non_clustered_leafs:
        for leaf in non_clustered_leafs:
            # local to remote tunnel
            vrouter_name = get_vrouter_name(module, local_switch)
            remote_ip = get_loopback_ip(module, leaf)
            tunnel_name = local_switch + '-to-' + leaf + '-tunnel'
            output += create_tunnel(module, tunnel_name, local_ip,
                                    remote_ip, vrouter_name, local_switch)
            output += add_vxlan_to_tunnel(module, vxlan, tunnel_name,
                                          local_switch)

            # Remote to local tunnel
            vrouter_name = get_vrouter_name(module, leaf)
            tunnel_name = leaf + '-to-' + local_switch + '-tunnel'
            output += create_tunnel(module, tunnel_name, remote_ip,
                                    local_ip, vrouter_name, leaf)
            output += add_vxlan_to_tunnel(module, vxlan, tunnel_name, leaf)

    return output


def configure_vtep_for_non_clustered_leafs(module, local_switch, vlan, vxlan):
    """
    Method to configure virtual tunnel end points for non clustered leafs.
    :param module: The Ansible module to fetch input parameters.
    :param local_switch: Name of the local switch.
    :param vlan: vlan id.
    :param vxlan: Vxlan to add to tunnel.
    :return: String describing output of configuration.
    """
    non_clustered_leafs = find_non_clustered_leafs(module)
    local_ip = get_loopback_ip(module, local_switch)
    output = ''
    for leaf in module.params['pn_leaf_list']:
        if leaf != local_switch:
            # local to remote tunnel
            if leaf in non_clustered_leafs:
                remote_ip = get_loopback_ip(module, leaf)
            else:
                remote_ip = get_vrouter_interface_ip(module, leaf, vlan)

            vrouter_name = get_vrouter_name(module, local_switch)
            tunnel_name = local_switch + '-to-' + leaf + '-tunnel'
            output += create_tunnel(module, tunnel_name, local_ip,
                                    remote_ip, vrouter_name, local_switch)
            output += add_vxlan_to_tunnel(module, vxlan, tunnel_name,
                                          local_switch)

            # Remote to local tunnel
            vrouter_name = get_vrouter_name(module, leaf)
            tunnel_name = leaf + '-to-' + local_switch + '-tunnel'
            output += create_tunnel(module, tunnel_name, remote_ip,
                                    local_ip, vrouter_name, leaf)
            output += add_vxlan_to_tunnel(module, vxlan, tunnel_name, leaf)

    return output


def add_vxlan_to_tunnel(module, vxlan, tunnel_name, switch):
    """
    Method to add vxlan to created tunnel so that it can carry vxlan traffic.
    :param module: The Ansible module to fetch input parameters.
    :param vxlan: vxlan id to add to tunnel.
    :param tunnel_name: Name of the tunnel on which vxlan will be added.
    :param switch: Name of the switch on which tunnel exists.
    :return: String describing if vxlan got added to tunnel or not.
    """
    global CHANGED_FLAG
    cli = pn_cli(module)
    cli += ' switch %s tunnel-vxlan-show format switch no-show-headers ' % (
        switch)
    existing_tunnel_vxlans = run_cli(module, cli).split()

    if tunnel_name not in existing_tunnel_vxlans:
        cli = pn_cli(module)
        cli += ' switch %s tunnel-vxlan-add name %s vxlan %s ' % (switch,
                                                                  tunnel_name,
                                                                  vxlan)
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


def find_non_clustered_leafs(module):
    """
    Method to find leafs which are not part of any cluster.
    :param module: The Ansible module to fetch input parameters.
    :return: The list of non clustered leaf switches.
    """
    non_clustered_leafs = []
    cli = pn_cli(module)
    clicopy = cli
    cli += ' cluster-show format cluster-node-1 no-show-headers '
    cluster_node_1 = run_cli(module, cli).split()
    cli = clicopy
    cli += ' cluster-show format cluster-node-2 no-show-headers '
    cluster_node_2 = run_cli(module, cli).split()

    for leaf in module.params['pn_leaf_list']:
        if (leaf not in cluster_node_1) and (leaf not in cluster_node_2):
            non_clustered_leafs.append(leaf)

    return non_clustered_leafs


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
        vlan_id = elements[0]
        leaf_switch_1 = elements[2]
        if len(elements) == 8:
            leaf_switch_2 = elements[3]
            vxlan_id = elements[6]
            loopback_port = elements[7]
            output += add_vxlan_to_vlan(module, vlan_id, vxlan_id)
            output += configure_vtep_for_clustered_leafs(module, leaf_switch_1,
                                                         vlan_id, vxlan_id)
            output += configure_vtep_for_clustered_leafs(module, leaf_switch_2,
                                                         vlan_id, vxlan_id)
            add_ports_to_vxlan_loopback_trunk(module, loopback_port)
        elif len(elements) == 5:
            vxlan_id = elements[3]
            loopback_port = elements[4]
            output += add_vxlan_to_vlan(module, vlan_id, vxlan_id)
            output += configure_vtep_for_non_clustered_leafs(
                module, leaf_switch_1, vlan_id, vxlan_id)
            add_ports_to_vxlan_loopback_trunk(module, loopback_port)

    return output


def main():
    """ This section is for arguments parsing """
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=False, type='str'),
            pn_clipassword=dict(required=False, type='str', no_log=True),
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

