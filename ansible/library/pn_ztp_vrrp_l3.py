#!/usr/bin/python
""" PN CLI VRRP L3 """

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
module: pn_ztp
author: 'Pluribus Networks (@gauravbajaj)'
modified by: 'Pluribus Networks (@saptaktakalkar)'
version: 1
short_description: CLI command to configure VRRP - Layer 3 Setup
description: Virtual Router Redundancy Protocol (VRRP) - Layer 3 Setup
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
    pn_fabric_name:
      description:
        - Specify name of the fabric.
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
    - name: VRRP L3 setup
      pn_ztp_vrrp_l3:
        pn_cliusername: "{{ USERNAME }}"
        pn_clipassword: "{{ PASSWORD }}"
        pn_fabric_name: 'ztp-fabric'
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


def create_vlan_l3(module, vlan_id):
    """
    Method to create vlans.
    :param module: The Ansible module to fetch input parameters.
    :param vlan_id: vlan id to be created.
    :return: String describing if vlan got created or if it already exists.
    """
    global CHANGED_FLAG
    output = ''
    cli = pn_cli(module)

    clicopy = cli
    clicopy += ' vlan-show format id no-show-headers '
    already_vlan_id = run_cli(module, clicopy).split()
    already_vlan_id = list(set(already_vlan_id))

    id_str = str(vlan_id)
    if id_str not in already_vlan_id:
        clicopy = cli
        clicopy += ' vlan-create id '
        clicopy += id_str
        clicopy += ' scope fabric '
        output += run_cli(module, clicopy)
        output += ' vlan with id ' + vlan_id + ' created! '
        CHANGED_FLAG.append(True)
    else:
        output += ' vlan with id ' + vlan_id + ' already exists! '
        CHANGED_FLAG.append(False)

    return output


def create_l3_vrouter(module, switch, vrrp_id):
    """
    Method to create vrouter and assign vrrp_id to the switches.
    :param module: The Ansible module to fetch input parameters.
    :param switch: The switch name on which vrouter will be created.
    :param vrrp_id: The vrrp_id to be assigned.
    :return: The output string informing details of vrouter created and
    interface added or if vrouter already exists.
    """
    global CHANGED_FLAG
    output = ''
    switch_temp = str(switch) + '-vrouter'
    vrouter_name = switch_temp
    vnet_name = module.params['pn_fabric_name'] + '-global'
    cli = pn_cli(module)
    cli += ' switch ' + switch
    cli_copy = cli

    # Check if vrouter already exists
    cli = cli_copy
    cli += ' vrouter-show format name no-show-headers '
    existing_vrouter_names = run_cli(module, cli).split()

    # If vrouter doesn't exists then create it
    if vrouter_name not in existing_vrouter_names:
        cli = cli_copy
        cli += ' vrouter-create name %s vnet %s hw-vrrp-id %s enable ' % (
            vrouter_name, vnet_name, vrrp_id)
        run_cli(module, cli)
        output += ' Created vrouter %s on switch %s! ' % (vrouter_name, switch)
        CHANGED_FLAG.append(True)
    else:
        output += ' Vrouter name %s on switch %s already exists! ' % (
            vrouter_name, switch)
        CHANGED_FLAG.append(False)

    return output


def create_l3_interface(module, switch, ip, vlan_id, vrrp_id,
                        ip_count, vrrp_priority):
    """
    Method to add vrouter interface and assign IP to it along with
    vrrp_id and vrrp_priority.
    :param module: The Ansible module to fetch input parameters.
    :param switch: The switch name on which vrouter will be created.
    :param ip: IP address to be assigned to vrouter interface.
    :param vlan_id: vlan_id to be assigned.
    :param vrrp_id: vrrp_id to be assigned.
    :param vrrp_priority: priority to be given(110 for active switch).
    :param ip_count: The value of fourth octet in the ip
    :return: The output string informing details of vrouter created and
    interface added or if vrouter already exists.
    """
    global CHANGED_FLAG
    output = ''
    cli = pn_cli(module)
    clicopy = cli

    cli += ' vrouter-show location %s format name no-show-headers ' % switch
    vrouter_name = run_cli(module, cli).split()
    ip_addr = ip.split('.')
    fourth_octet = ip_addr[3].split('/')
    subnet = fourth_octet[1]

    static_ip = ip_addr[0] + '.' + ip_addr[1] + '.' + ip_addr[2] + '.'
    ip1 = static_ip + '1' + '/' + subnet
    ip2 = static_ip + ip_count + '/' + subnet

    cli = clicopy
    cli += ' vrouter-interface-show vlan %s ip %s ' % (vlan_id, ip2)
    cli += ' format switch no-show-headers '
    existing_vrouter = run_cli(module, cli).split()
    existing_vrouter = list(set(existing_vrouter))

    if vrouter_name[0] not in existing_vrouter:
        cli = clicopy
        cli += ' vrouter-interface-add vrouter-name ' + vrouter_name[0]
        cli += ' ip ' + ip2
        cli += ' vlan %s if data ' % vlan_id
        run_cli(module, cli)
        output += ' Added vrouter interface with ip %s! ' % ip2
        CHANGED_FLAG.append(True)
    else:
        output += ' Interface already exists for vrouter %s! ' % vrouter_name[0]
        CHANGED_FLAG.append(False)

    cli = clicopy
    cli += ' vrouter-interface-show vrouter-name %s ip %s vlan %s ' % (
        vrouter_name[0], ip2, vlan_id)
    cli += ' format nic no-show-headers '
    eth_port = run_cli(module, cli).split()
    eth_port.remove(vrouter_name[0])

    cli = clicopy
    cli += ' vrouter-interface-show vlan %s ip %s vrrp-primary %s ' % (
        vlan_id, ip1, eth_port[0])
    cli += ' format switch no-show-headers '
    existing_vrouter = run_cli(module, cli).split()
    existing_vrouter = list(set(existing_vrouter))

    if vrouter_name[0] not in existing_vrouter:
        cli = clicopy
        cli += ' vrouter-interface-add vrouter-name ' + vrouter_name[0]
        cli += ' ip ' + ip1
        cli += ' vlan %s if data vrrp-id %s ' % (vlan_id, vrrp_id)
        cli += ' vrrp-primary %s vrrp-priority %s ' % (eth_port[0],
                                                       vrrp_priority)
        run_cli(module, cli)
        output += ' Added vrouter interface with ip %s ' % ip1
        CHANGED_FLAG.append(True)

    else:
        output += ' Interface already exists for vrouter %s! ' % vrouter_name[0]
        CHANGED_FLAG.append(False)

    return output


def leaf_no_cluster(module, leaf_list):
    """
    Method to find non clustered leaf nodes.
    :param module: The Ansible module to fetch input parameters.
    :param leaf_list: The list of all the leaf switches.
    :return: The list of non clustered leaf switches.
    """
    cli = pn_cli(module)
    non_cluster_leaf = []
    clicopy = cli
    clicopy += ' cluster-show format cluster-node-1 no-show-headers '
    cluster1 = run_cli(module, clicopy).split()

    clicopy = cli
    clicopy += ' cluster-show format cluster-node-2 no-show-headers '
    cluster2 = run_cli(module, clicopy).split()

    for leaf in leaf_list:
        if (leaf not in cluster1) and (leaf not in cluster2):
            non_cluster_leaf.append(leaf)

    return non_cluster_leaf


def create_cluster(module, switch, name, node1, node2):
    """
    Method to create a cluster between two switches.
    :param module: The Ansible module to fetch input parameters.
    :param switch: Name of the local switch.
    :param name: The name of the cluster to create.
    :param node1: First node of the cluster.
    :param node2: Second node of the cluster.
    :return: The output of run_cli() method.
    """
    global CHANGED_FLAG
    cli = pn_cli(module)
    clicopy = cli
    cli += ' switch %s cluster-show format name no-show-headers ' % node1
    cluster_list = run_cli(module, cli).split()
    if name not in cluster_list:
        cli = clicopy
        cli += ' switch %s cluster-create name %s ' % (switch, name)
        cli += ' cluster-node-1 %s cluster-node-2 %s ' % (node1, node2)
        if 'Success' in run_cli(module, cli):
            CHANGED_FLAG.append(True)
            return ' %s created successfully! ' % name
    else:
        CHANGED_FLAG.append(False)
        return ' %s already exists! ' % name


def leaf_cluster_formation(module, non_cluster_leaf, spine_list):
    """
    This method uses non-clustered leafs and forms cluster.
    :param module: The Ansible module to fetch input parameters.
    :param non_cluster_leaf: List of all the leaf not in cluster.
    :param spine_list: The list of spines.
    :return: The output message of success or error
    """
    cli = pn_cli(module)
    clicopy = cli
    output = ''
    flag = 0
    while flag == 0:
        if len(non_cluster_leaf) == 0:
            output += ' no more leafs to create cluster '
            flag += 1
        else:
            node1 = non_cluster_leaf[0]
            non_cluster_leaf.remove(node1)
            cli = clicopy
            cli += ' switch %s lldp-show format sys-name ' % node1
            cli += ' no-show-headers '
            system_names = run_cli(module, cli).split()
            system_names = list(set(system_names))

            flag1 = 0
            switch_count = 0
            while (switch_count < len(system_names)) and (flag1 == 0):
                switch = system_names[switch_count]
                if switch not in spine_list:
                    if switch in non_cluster_leaf:
                        name = node1 + '-to-' + switch + '-cluster'
                        output += create_cluster(module, switch, name, node1,
                                                 switch)
                        non_cluster_leaf.remove(switch)
                        flag1 += 1
                    else:
                        output += ' switch already has a cluster '
                else:
                    output += ' switch is a spine '

                switch_count += 1

    return output


def create_leaf_cluster(module):
    """
    This method creates leaf cluster with physical link.
    :param module: The Ansible module to fetch input parameters.
    :return: The output message with success or error.
    """
    output = ''
    spine_list = module.params['pn_spine_list']
    leaf_list = module.params['pn_leaf_list']
    non_cluster_leaf = leaf_no_cluster(module, leaf_list)
    output += leaf_cluster_formation(module, non_cluster_leaf, spine_list)
    return output


def create_l3_vrouter_novrrp(module, switch):
    """
    Method to create vrouter and assign vrrp_id to the switches.
    :param module: The Ansible module to fetch input parameters.
    :param switch: The switch name on which vrouter will be created.
    :return: The output string informing details of vrouter created and
    interface added or if vrouter already exists.
    """
    global CHANGED_FLAG
    output = ''
    switch_temp = str(switch) + '-vrouter'
    vrouter_name = switch_temp
    vnet_name = module.params['pn_fabric_name'] + '-global'
    cli = pn_cli(module)
    cli += ' switch ' + switch
    cli_copy = cli

    # Check if vrouter already exists
    cli = cli_copy
    cli += ' vrouter-show format name no-show-headers '
    existing_vrouter_names = run_cli(module, cli).split()

    # If vrouter doesn't exists then create it
    if vrouter_name not in existing_vrouter_names:
        cli = cli_copy
        cli += ' vrouter-create name %s vnet %s ' % (
            vrouter_name, vnet_name)
        run_cli(module, cli)
        output += ' Created vrouter %s on switch %s! ' % (vrouter_name, switch)
        CHANGED_FLAG.append(True)
    else:
        output += ' Vrouter name %s on switch %s already exists! ' % (
            vrouter_name, switch)
        CHANGED_FLAG.append(False)

    return output


def vrrp_noncluster_switch(module, ip, noncluster_leaf, vlan_id):
    """
    Method to configure vrrp for non-cluster switches
    :param module: The Ansible module to fetch input parameters.
    :param ip: ip address for the default gateway
    :param noncluster_leaf: name of all the non-cluster leaf
    :param vlan_id: The vlan id to be assigned.
    :return: It returns the output in the success or failure
    """
    global CHANGED_FLAG
    output = ''
    cli = pn_cli(module)
    clicopy = cli

    for switch in noncluster_leaf:
        cli = clicopy
        cli += ' vrouter-show location %s format name no-show-headers ' % switch
        vrouter_name = run_cli(module, cli).split()
        ip_addr = ip.split('.')
        fourth_octet = ip_addr[3].split('/')
        subnet = fourth_octet[1]

        static_ip = ip_addr[0] + '.' + ip_addr[1] + '.' + ip_addr[2] + '.'
        ip1 = static_ip + '1' + '/' + subnet

        cli = clicopy
        cli += ' vrouter-interface-show ip %s vlan %s ' % (ip1, vlan_id)
        cli += ' format switch no-show-headers '
        existing_vrouter = run_cli(module, cli).split()
        existing_vrouter = list(set(existing_vrouter))

        if vrouter_name[0] not in existing_vrouter:
            cli = clicopy
            cli += ' vrouter-interface-add vrouter-name ' + vrouter_name[0]
            cli += ' vlan ' + vlan_id
            cli += ' ip ' + ip1
            run_cli(module, cli)
            output += ' Added vrouter interface with ip %s ' % ip1
            CHANGED_FLAG.append(True)
        else:
            output += ' Interface already exists for vrouter ' + vrouter_name[0]
            output += ' '
            CHANGED_FLAG.append(False)

    return output


def configure_vrrp_l3_with_cluster(module, vrrp_id, vrrp_ip,
                                   active_switch, vlan_id, switch_list):
    """
    Method to configure vrrp interfaces.
    :param module: The Ansible module to fetch input parameters.
    :param vrrp_id: The vrrp_id need to be assigned.
    :param vrrp_ip: The vrrp_ip needed to be assigned.
    :param active_switch: The name of the active switch.
    :param vlan_id: vlan id to be assigned.
    :param switch_list: List of switches.
    :return: It returns the output of the configuration
    """
    output = ''
    node1 = switch_list[0]
    node2 = switch_list[1]
    name = node1 + '-to-' + node2 + '-cluster'
    output += create_cluster(module, node2, name, node1,
                             node2)

    output += create_vlan_l3(module, vlan_id)
    host_count = 1

    for switch in switch_list:
        output += create_l3_vrouter(module, switch, vrrp_id)

    for switch in switch_list:
        host_count += 1
        if switch == active_switch:
            vrrp_priority = '110'
        else:
            vrrp_priority = '100'

        output += create_l3_interface(module, switch, vrrp_ip, vlan_id,
                                      vrrp_id, str(host_count),
                                      vrrp_priority)

    return output


def configure_vrrp_l3_without_cluster(module, vlan_id, ip, noncluster_leaf):
    """
    Method to configure VRRP for non clustered leafs.
    :param module: The Ansible module to fetch input parameters.
    :param vlan_id: vlan id to be assigned.
    :param ip: Ip address to be assigned.
    :param noncluster_leaf: Non clustered leaf switch.
    :return: Output string of configuration.
    """
    output = ' '
    for switch in noncluster_leaf:
        output += create_l3_vrouter_novrrp(module, switch)

    output += create_vlan_l3(module, vlan_id)
    output += vrrp_noncluster_switch(module, ip, noncluster_leaf, vlan_id)
    return output


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
    cli += ' tunnel-vxlan-show format name no-show-headers '
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


def configure_vrrp_l3(module, csv_data):
    """
    Method to configure VRRP L3.
    :param module: The Ansible module to fetch input parameters.
    :param csv_data: String containing vrrp data parsed from csv file.
    :return: Output string of configuration.
    """
    output = ''
    spine_list = module.params['pn_spine_list']

    for switch in spine_list:
        output += create_l3_vrouter_novrrp(module, switch)

    csv_data = csv_data.replace(" ", "")
    csv_data_list = csv_data.split('\n')
    for row in csv_data_list:
        elements = row.split(',')
        if len(elements) > 3:
            if len(elements) <= 6:
                switch_list = []
                vlan_id = elements[0]
                vrrp_ip = elements[1]
                switch_list.append(str(elements[2]))
                switch_list.append(str(elements[3]))
                vrrp_id = elements[4]
                active_switch = str(elements[5])
                output += configure_vrrp_l3_with_cluster(module, vrrp_id,
                                                         vrrp_ip, active_switch,
                                                         vlan_id, switch_list)
            else:
                pass    # TODO: Add logic to call vxlan code.

        else:
            noncluster_leaf = []
            vlan_id = elements[0]
            ip = elements[1]
            noncluster_leaf.append(str(elements[2]))
            output += configure_vrrp_l3_without_cluster(module, vlan_id, ip,
                                                        noncluster_leaf)

    return output


def main():
    """ This section is for arguments parsing """
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=False, type='str'),
            pn_clipassword=dict(required=False, type='str', no_log=True),
            pn_fabric_name=dict(required=True, type='str'),
            pn_spine_list=dict(required=False, type='list'),
            pn_leaf_list=dict(required=False, type='list'),
            pn_csv_data=dict(required=True, type='str'),
        )
    )

    global CHANGED_FLAG
    CHANGED_FLAG = []
    message = configure_vrrp_l3(module, module.params['pn_csv_data'])

    module.exit_json(
        stdout=message,
        error='0',
        failed=False,
        msg='VRRP Layer 3 Setup completed successfully.',
        changed=True if True in CHANGED_FLAG else False
    )


if __name__ == '__main__':
    main()

