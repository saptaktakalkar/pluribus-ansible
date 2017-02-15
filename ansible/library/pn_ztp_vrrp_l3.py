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


def create_vlan(module, vlan_id):
    """
    Method to create vlans.
    :param module: The Ansible module to fetch input parameters.
    :param vlan_id: vlan id to be created.
    :return: String describing if vlan got created or if it already exists.
    """
    global CHANGED_FLAG
    cli = pn_cli(module)
    clicopy = cli
    cli += ' vlan-show format id no-show-headers '
    existing_vlan_ids = run_cli(module, cli).split()
    existing_vlan_ids = list(set(existing_vlan_ids))

    if vlan_id not in existing_vlan_ids:
        cli = clicopy
        cli += ' vlan-create id ' + vlan_id
        cli += ' scope fabric '
        run_cli(module, cli)
        output = ' vlan with id ' + vlan_id + ' created! '
        CHANGED_FLAG.append(True)
    else:
        output = ' vlan with id ' + vlan_id + ' already exists! '
        CHANGED_FLAG.append(False)

    return output


def create_vrouter(module, switch, vrrp_id):
    """
    Method to create vrouter and assign vrrp_id to the switches.
    :param module: The Ansible module to fetch input parameters.
    :param switch: The switch name on which vrouter will be created.
    :param vrrp_id: The vrrp_id to be assigned.
    :return: String describing if vrouter got created or if it already exists.
    """
    global CHANGED_FLAG
    output = ''
    vrouter_name = str(switch) + '-vrouter'
    vnet_name = module.params['pn_fabric_name'] + '-global'
    cli = pn_cli(module)
    cli += ' switch ' + switch
    clicopy = cli

    # Check if vrouter already exists
    cli += ' vrouter-show format name no-show-headers '
    existing_vrouter_names = run_cli(module, cli).split()

    # If vrouter doesn't exists then create it
    if vrouter_name not in existing_vrouter_names:
        cli = clicopy
        cli += ' vrouter-create name %s vnet %s hw-vrrp-id %s enable ' % (
            vrouter_name, vnet_name, vrrp_id)
        run_cli(module, cli)
        output += ' Created vrouter %s on switch %s! ' % (vrouter_name, switch)
        CHANGED_FLAG.append(True)
    else:
        cli = clicopy
        cli += ' vrouter-show name ' + vrouter_name
        cli += ' format hw-vrrp-id no-show-headers'
        hw_vrrp_id = run_cli(module, cli).split()[0]
        if hw_vrrp_id == vrrp_id:
            output += ' Vrouter name %s on switch %s already exists! ' % (
                vrouter_name, switch)
            CHANGED_FLAG.append(False)
        else:
            cli = clicopy
            cli += ' vrouter-modify name %s hw-vrrp-id %s ' % (
                vrouter_name, vrrp_id)
            run_cli(module, cli)
            output += ' Modified hw-vrrp-id on vrouter %s on switch %s! ' % (
                   vrouter_name, switch)
            CHANGED_FLAG.append(True)
    return output


def create_vrouter_interface(module, switch, ip, vlan_id, vrrp_id,
                             ip_count, vrrp_priority):
    """
    Method to add vrouter interface and assign IP to it along with
    vrrp_id and vrrp_priority.
    :param module: The Ansible module to fetch input parameters.
    :param switch: The switch name on which interfaces will be created.
    :param ip: IP address to be assigned to vrouter interface.
    :param vlan_id: vlan_id to be assigned.
    :param vrrp_id: vrrp_id to be assigned.
    :param vrrp_priority: priority to be given(110 for active switch).
    :param ip_count: The value of fourth octet in the ip
    :return: String describing if vrouter interface got added or not.
    """
    global CHANGED_FLAG
    vrouter_name = get_vrouter_name(module, switch)
    ip_addr = ip.split('.')
    fourth_octet = ip_addr[3].split('/')
    subnet = fourth_octet[1]

    static_ip = ip_addr[0] + '.' + ip_addr[1] + '.' + ip_addr[2] + '.'
    ip1 = static_ip + '1' + '/' + subnet
    ip2 = static_ip + ip_count + '/' + subnet

    cli = pn_cli(module)
    clicopy = cli
    cli += ' vrouter-interface-show vlan %s ip %s ' % (vlan_id, ip2)
    cli += ' format switch no-show-headers '
    existing_vrouter = run_cli(module, cli).split()
    existing_vrouter = list(set(existing_vrouter))

    if vrouter_name not in existing_vrouter:
        cli = clicopy
        cli += ' switch ' + switch
        cli += ' vrouter-interface-add vrouter-name ' + vrouter_name
        cli += ' ip ' + ip2
        cli += ' vlan %s if data ' % vlan_id
        run_cli(module, cli)
        output = ' Added vrouter interface with ip %s to %s!' % (ip2,
                                                                 vrouter_name)
        CHANGED_FLAG.append(True)
    else:
        output = ' Interface %s already exists for vrouter %s! ' % (
            ip2, vrouter_name)
        CHANGED_FLAG.append(False)

    cli = clicopy
    cli += ' vrouter-interface-show vrouter-name %s ip %s vlan %s ' % (
        vrouter_name, ip2, vlan_id)
    cli += ' format nic no-show-headers '
    eth_port = run_cli(module, cli).split()
    eth_port.remove(vrouter_name)

    cli = clicopy
    cli += ' vrouter-interface-show vlan %s ip %s vrrp-primary %s ' % (
        vlan_id, ip1, eth_port[0])
    cli += ' format switch no-show-headers '
    existing_vrouter = run_cli(module, cli).split()
    existing_vrouter = list(set(existing_vrouter))

    if vrouter_name not in existing_vrouter:
        cli = clicopy
        cli += ' switch ' + switch
        cli += ' vrouter-interface-add vrouter-name ' + vrouter_name
        cli += ' ip ' + ip1
        cli += ' vlan %s if data vrrp-id %s ' % (vlan_id, vrrp_id)
        cli += ' vrrp-primary %s vrrp-priority %s ' % (eth_port[0],
                                                       vrrp_priority)
        run_cli(module, cli)
        output += ' Added vrouter interface with ip %s to %s! ' % (ip1,
                                                                   vrouter_name)
        CHANGED_FLAG.append(True)

    else:
        output += ' Interface %s already exists for vrouter %s! ' % (
            ip1, vrouter_name)
        CHANGED_FLAG.append(False)

    return output


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


def create_vrouter_without_vrrp(module, switch):
    """
    Method to create vrouter without assigning vrrp id to it.
    :param module: The Ansible module to fetch input parameters.
    :param switch: The switch name on which vrouter will be created.
    :return: String describing if vrouter got created or if it already exists.
    """
    global CHANGED_FLAG
    vrouter_name = str(switch) + '-vrouter'
    vnet_name = module.params['pn_fabric_name'] + '-global'
    cli = pn_cli(module)
    cli += ' switch ' + switch
    clicopy = cli

    # Check if vrouter already exists
    cli += ' vrouter-show format name no-show-headers '
    existing_vrouter_names = run_cli(module, cli).split()

    # If vrouter doesn't exists then create it
    if vrouter_name not in existing_vrouter_names:
        cli = clicopy
        cli += ' vrouter-create name %s vnet %s ' % (vrouter_name, vnet_name)
        run_cli(module, cli)
        output = ' Created vrouter %s on switch %s! ' % (vrouter_name, switch)
        CHANGED_FLAG.append(True)
    else:
        output = ' Vrouter name %s on switch %s already exists! ' % (
            vrouter_name, switch)
        CHANGED_FLAG.append(False)

    return output


def configure_vrrp_for_non_cluster_leafs(module, ip, non_cluster_leaf, vlan_id):
    """
    Method to configure vrrp for non-cluster switches.
    :param module: The Ansible module to fetch input parameters.
    :param ip: IP address for the default gateway
    :param non_cluster_leaf: Name of non-cluster leaf switch.
    :param vlan_id: The vlan id to be assigned.
    :return: String describing whether interfaces got added or not.
    """
    global CHANGED_FLAG
    vrouter_name = get_vrouter_name(module, non_cluster_leaf)
    
    ip_addr = ip.split('.')
    fourth_octet = ip_addr[3].split('/')
    subnet = fourth_octet[1]

    static_ip = ip_addr[0] + '.' + ip_addr[1] + '.' + ip_addr[2] + '.'
    ip1 = static_ip + '1' + '/' + subnet

    cli = pn_cli(module)
    clicopy = cli
    cli += ' vrouter-interface-show ip %s vlan %s ' % (ip1, vlan_id)
    cli += ' format switch no-show-headers '
    existing_vrouter = run_cli(module, cli).split()
    existing_vrouter = list(set(existing_vrouter))

    if vrouter_name not in existing_vrouter:
        cli = clicopy
        cli += ' vrouter-interface-add vrouter-name ' + vrouter_name
        cli += ' vlan ' + vlan_id
        cli += ' ip ' + ip1
        run_cli(module, cli)
        output = ' Added vrouter interface with ip %s ' % ip1
        CHANGED_FLAG.append(True)
    else:
        output = ' Interface already exists for vrouter ' + vrouter_name
        CHANGED_FLAG.append(False)

    return output


def configure_vrrp_for_clustered_switches(module, vrrp_id, vrrp_ip,
                                          active_switch, vlan_id, switch_list):
    """
    Method to configure vrrp interfaces for clustered leaf switches.
    :param module: The Ansible module to fetch input parameters.
    :param vrrp_id: The vrrp_id to be assigned.
    :param vrrp_ip: The vrrp_ip to be assigned.
    :param active_switch: The name of the active switch.
    :param vlan_id: vlan id to be assigned.
    :param switch_list: List of clustered switches.
    :return: The output of the configuration.
    """
    node1 = switch_list[0]
    node2 = switch_list[1]
    name = node1 + '-to-' + node2 + '-cluster'
    host_count = 1
    
    output = create_cluster(module, node2, name, node1, node2)
    output += create_vlan(module, vlan_id)

    for switch in switch_list:
        output += create_vrouter(module, switch, vrrp_id)

    for switch in switch_list:
        host_count += 1
        vrrp_priority = '110' if switch == active_switch else '100'
        output += create_vrouter_interface(module, switch, vrrp_ip, vlan_id,
                                           vrrp_id, str(host_count),
                                           vrrp_priority)

    return output


def configure_vrrp_for_non_clustered_switches(module, vlan_id, ip,
                                              non_cluster_leaf):
    """
    Method to configure VRRP for non clustered leafs.
    :param module: The Ansible module to fetch input parameters.
    :param vlan_id: vlan id to be assigned.
    :param ip: Ip address to be assigned.
    :param non_cluster_leaf: Name of non-clustered leaf switch.
    :return: Output string of configuration.
    """
    output = create_vrouter_without_vrrp(module, non_cluster_leaf)
    output += create_vlan(module, vlan_id)
    output += configure_vrrp_for_non_cluster_leafs(module, ip, 
                                                   non_cluster_leaf, vlan_id)
    return output


def configure_vrrp(module, csv_data):
    """
    Method to configure VRRP L3.
    :param module: The Ansible module to fetch input parameters.
    :param csv_data: String containing vrrp data parsed from csv file.
    :return: Output string of configuration.
    """
    output = ''
    for switch in module.params['pn_spine_list']:
        output += create_vrouter_without_vrrp(module, switch)

    csv_data = csv_data.replace(" ", "")
    csv_data_list = csv_data.split('\n')
    # Parse csv file data and configure VRRP.
    for row in csv_data_list:
        elements = row.split(',')
        switch_list = []
        vlan_id = elements[0]
        vrrp_ip = elements[1]
        leaf_switch_1 = str(elements[2])
        if len(elements) > 5:
            leaf_switch_2 = str(elements[3])
            vrrp_id = elements[4]
            active_switch = str(elements[5])
            switch_list.append(leaf_switch_1)
            switch_list.append(leaf_switch_2)
            output += configure_vrrp_for_clustered_switches(module, vrrp_id,
                                                            vrrp_ip,
                                                            active_switch,
                                                            vlan_id,
                                                            switch_list)

        else:
            output += configure_vrrp_for_non_clustered_switches(module, vlan_id,
                                                                vrrp_ip,
                                                                leaf_switch_1)

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
    message = configure_vrrp(module, module.params['pn_csv_data'])

    module.exit_json(
        stdout=message,
        error='0',
        failed=False,
        msg='VRRP Layer 3 Setup completed successfully.',
        changed=True if True in CHANGED_FLAG else False
    )


if __name__ == '__main__':
    main()

