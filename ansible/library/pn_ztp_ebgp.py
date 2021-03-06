#!/usr/bin/python
""" PN CLI Zero Touch Provisioning (ZTP) with EBGP"""

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

DOCUMENTATION = """
---
module: pn_ztp_ebgp
author: "Pluribus Networks (@gauravbajaj)"
version: 1
short_description: CLI command to do zero touch provisioning with ebgp.
description:
    Zero Touch Provisioning (ZTP) allows you to provision new switches in your
    network automatically, without manual intervention.
    It performs following steps:
        - Assigning bgp_as
        - Configuring bgp_redistribute
        - Configuring bgp_maxpath
        - Assign bgp_neighbor
        - Assign router_id
        - Create leaf_cluster
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
    cliswitch = module.params['pn_cliswitch']
    if username and password:
        cli = '/usr/bin/cli --quiet --user %s:%s' % (username, password)
    else:
        cli = '/usr/bin/cli --quiet '

    if cliswitch:
        cli += ' switch ' + cliswitch

    return cli


def run_cli(module, cli):
    """
    This method executes the cli command on the target node(s) and returns the
    output.
    :param module: The Ansible module to fetch input parameters.
    :param cli: the complete cli string to be executed on the target node(s).
    :return: Output/Error or Success message depending upon the
    response from cli.
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


def assign_bgp_as(module, bgp_as):
    """
    This method assigns bgp_as to vrouter.
    :param module: The Ansible module to fetch input parameters.
    :param bgp_as: The user_input for the bgp_as to be assigned.
    :return: The output message of the assignment of the bgp_as
    """
    output = ' '
    bgp_as_spine = bgp_as
    bgp_leaf = int(bgp_as) + 1
    spine_list = module.params['pn_spine_list']
    cli = pn_cli(module)
    if 'switch' in cli:
        cli = cli.rpartition('switch')[0]

    clicopy = cli
    cli += ' vrouter-show format name no-show-headers '
    vrouter_names = run_cli(module, cli).split()

    if len(vrouter_names) > 0:
        for vrouter in vrouter_names:
            cli = clicopy
            cli += ' vrouter-show name ' + vrouter
            cli += ' format location no-show-headers '
            switch_vrouter = run_cli(module, cli).split()
            if switch_vrouter[0] in spine_list:
                cli = clicopy
                cli += ' vrouter-modify name %s bgp-as %s ' % (vrouter,
                                                               bgp_as_spine)
                output += run_cli(module, cli)
                output += ' '
            else:
                cli = clicopy
                cli += ' vrouter-modify name %s bgp-as %s ' % (vrouter,
                                                               str(bgp_leaf))
                output += run_cli(module, cli)
                output += ' '
                bgp_leaf += 1
    else:
        output += "No vrouters present!"

    return output


def bgp_neighbor(module):
    """
    This method add bgp_neighbor to the vrouter.
    :param module: The Ansible module to fetch input parameters.
    :return: The output of the adding bgp-neighbor.
    """
    output = ' '
    cli = pn_cli(module)
    if 'switch' in cli:
        cli = cli.rpartition('switch')[0]

    clicopy = cli
    cli += ' vrouter-show format name no-show-headers '
    vrouter_names = run_cli(module, cli).split()

    if len(vrouter_names) > 0:
        for vrouter in vrouter_names:
            cli = clicopy
            cli += ' vrouter-show name ' + vrouter
            cli += ' format location no-show-headers '
            switch = run_cli(module, cli).split()

            cli = clicopy
            cli += ' vrouter-interface-show vrouter-name ' + vrouter
            cli += ' format l3-port no-show-headers '
            port_num = run_cli(module, cli).split()
            port_num = list(set(port_num))
            port_num.remove(vrouter)

            for port in port_num:
                cli = clicopy
                cli += ' switch %s port-show port %s ' % (switch[0], port)
                cli += ' format hostname no-show-headers '
                hostname = run_cli(module, cli).split()

                cli = clicopy
                cli += ' vrouter-show location ' + hostname[0]
                cli += ' format bgp-as no-show-headers '
                bgp_hostname = run_cli(module, cli).split()

                cli = clicopy
                cli += ' switch %s port-show port %s ' % (switch[0], port)
                cli += ' format rport no-show-headers '
                port_hostname = run_cli(module, cli)

                cli = clicopy
                cli += ' vrouter-show location ' + hostname[0]
                cli += ' format name no-show-headers '
                vrouter_hostname = run_cli(module, cli).split()

                cli = clicopy
                cli += ' vrouter-interface-show '
                cli += ' vrouter-name ' + vrouter_hostname[0]
                cli += ' l3-port %s format ip no-show-headers ' % port_hostname
                ip_hostname_subnet = run_cli(module, cli).split()
                ip_hostname_subnet.remove(vrouter_hostname[0])

                ip_hostname_subnet = ip_hostname_subnet[0].split('/')
                ip_hostname = ip_hostname_subnet[0]

                cli = clicopy
                cli += ' vrouter-bgp-show remote-as %s neighbor %s ' % (
                    bgp_hostname[0], ip_hostname)
                cli += ' format switch no-show-headers '
                already_added = run_cli(module, cli).split()

                if vrouter in already_added:
                    output += " BGP already exists in " + vrouter
                    output += ' '
                else:
                    cli = clicopy
                    cli += ' vrouter-bgp-add vrouter-name ' + vrouter
                    cli += ' neighbor %s remote-as %s ' % (ip_hostname,
                                                           bgp_hostname[0])
                    output += run_cli(module, cli)
                    output += ' Added bgp ' + vrouter
    else:
        print "No vrouter created yet!"

    return output


def assign_router_id(module):
    """
    This method assign router id, which is same as loop back ip.
    :param module: The Ansible module to fetch input parameters.
    :return: The output message for the assignment.
    """
    output = ' '
    cli = pn_cli(module)
    if 'switch' in cli:
        cli = cli.rpartition('switch')[0]

    clicopy = cli
    cli += ' vrouter-show format name no-show-headers '
    vrouter_names = run_cli(module, cli).split()
    if len(vrouter_names) > 0:
        for vrouter in vrouter_names:
            cli = clicopy
            cli += ' vrouter-loopback-interface-show vrouter-name ' + vrouter
            cli += ' format ip no-show-headers '
            loopback_ip = run_cli(module, cli).split()
            loopback_ip.remove(vrouter)

            cli = clicopy
            cli += ' vrouter-modify name %s router-id %s ' % (vrouter,
                                                              loopback_ip[0])
            output += run_cli(module, cli)
            output += ' '
    else:
        print "No vrouters"

    return output


def assign_bgp_redistribute(module, bgp_redistribute):
    """
    This method assigns bgp_redistribute to the vrouter.
    :param module: The Ansible module to fetch input parameters.
    :param bgp_redistribute: It is 'connected' by default.
    :return: The output message for the assignment.
    """
    output = ' '
    cli = pn_cli(module)
    if 'switch' in cli:
        cli = cli.rpartition('switch')[0]

    clicopy = cli
    cli += ' vrouter-show format name no-show-headers '
    vrouter_names = run_cli(module, cli).split()

    for vrouter in vrouter_names:
        cli = clicopy
        cli += ' vrouter-modify name ' + vrouter
        cli += ' bgp-redistribute ' + bgp_redistribute
        output += run_cli(module, cli)
        output += ' '

    return output


def assign_bgp_maxpath(module, bgp_maxpath):
    """
    This method assigns bgp_maxpath to the vrouter.
    :param module: The Ansible module to fetch input parameters.
    :param bgp_maxpath: It is '16' by default.
    :return: The output message for the assignment.
    """
    output = ' '
    cli = pn_cli(module)
    if 'switch' in cli:
        cli = cli.rpartition('switch')[0]

    clicopy = cli
    cli += ' vrouter-show format name no-show-headers '
    vrouter_names = run_cli(module, cli).split()

    for vrouter in vrouter_names:
        cli = clicopy
        cli += ' vrouter-modify name %s bgp-max-paths %s ' % (vrouter,
                                                              bgp_maxpath)
        output += run_cli(module, cli)
        output += ' '

    return output


def leaf_no_cluster(module, leaf_list):
    """
    This method is to find leafs not in present in any cluster.
    :param module: The Ansible module to fetch input parameters.
    :param leaf_list: The list of all the leaf switches.
    :return: The list of leaf in no cluster.
    """
    cli = pn_cli(module)
    non_cluster_leaf = []
    if 'switch' in cli:
        cli = cli.rpartition('switch')[0]

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
    This method is to create a cluster between two switches.
    :param module: The Ansible module to fetch input parameters.
    :param switch: Name of the local switch.
    :param name: The name of the cluster to create.
    :param node1: First node of the cluster.
    :param node2: Second node of the cluster.
    :return: The output of run_cli() method.
    """
    cli = pn_cli(module)
    if 'switch' in cli:
        cli = cli.rpartition('switch')[0]

    clicopy = cli
    cli += ' switch %s cluster-show format name no-show-headers ' % node1
    cluster_list = run_cli(module, cli).split()
    if name not in cluster_list:
        cli = clicopy
        cli += ' switch %s cluster-create name %s ' % (switch, name)
        cli += ' cluster-node-1 %s cluster-node-2 %s ' % (node1, node2)
        return run_cli(module, cli)
    else:
        return "Already part of a cluster"


def leaf_cluster_formation(module, non_cluster_leaf, spine_list):
    """
    This method uses non-clustered leafs and forms cluster.
    :param module: The Ansible module to fetch input parameters.
    :param non_cluster_leaf: List of all the leaf not in cluster.
    :param spine_list: The list of spines.
    :return: The output message of success or error.
    """

    cli = pn_cli(module)
    if 'switch' in cli:
        cli = cli.rpartition('switch')[0]

    clicopy = cli
    output = ' '
    flag = 0
    while flag == 0:
        if len(non_cluster_leaf) == 0:
            output += "no more leaf to create cluster"
            output += ' '
            flag += 1
        else:
            node1 = non_cluster_leaf[0]
            non_cluster_leaf.remove(node1)
            cli = clicopy
            cli += ' switch %s lldp-show ' % node1
            cli += ' format sys-name no-show-headers '
            system_names = run_cli(module, cli).split()
            system_names = list(set(system_names))

            flag1 = 0
            i = 0
            while (i < len(system_names)) and (flag1 == 0):
                switch = system_names[i]
                if switch not in spine_list:
                    if switch in non_cluster_leaf:
                        name = node1 + '-to-' + switch + '-cluster'
                        output += create_cluster(module, switch, name, node1,
                                                 switch)
                        output += ' '
                        non_cluster_leaf.remove(switch)
                        flag1 += 1
                    else:
                        print "Switch already has a cluster"
                else:
                    print "Switch is a spine"

                i += 1

    return output


def create_leaf_cluster(module):
    """
    This method creates leaf cluster with physical link.
    :param module: The Ansible module to fetch input parameters.
    :return: The output message with success or error.
    """
    output = ' '
    spine_list = module.params['pn_spine_list']
    leaf_list = module.params['pn_leaf_list']
    non_cluster_leaf = leaf_no_cluster(module, leaf_list)
    output += leaf_cluster_formation(module, non_cluster_leaf, spine_list)
    output += ' '
    return output


def main():
    """ This section is for arguments parsing """

    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=False, type='str'),
            pn_clipassword=dict(required=False, type='str', no_log=True),
            pn_cliswitch=dict(required=False, type='str'),
            pn_fabric_name=dict(required=False, type='str'),
            pn_fabric_network=dict(required=False, type='str',
                                   choices=['mgmt', 'in-band'],
                                   default='mgmt'),
            pn_fabric_type=dict(required=False, type='str',
                                choices=['layer2', 'layer3'],
                                default='layer2'),
            pn_fabric_retry=dict(required=False, type='int', default=1),
            pn_run_l2_l3=dict(required=False, type='bool', default=False),
            pn_net_address=dict(required=False, type='str'),
            pn_cidr=dict(required=False, type='str'),
            pn_supernet=dict(required=False, type='str'),
            pn_spine_list=dict(required=False, type='list'),
            pn_leaf_list=dict(required=False, type='list'),
            pn_update_fabricto_inband=dict(required=False, type='bool',
                                           default=False),
            pn_assign_loopback=dict(required=False, type='bool', default=False),
            pn_loopback_ip=dict(required=False, type='str',
                                default='101.101.101.0/32'),
            pn_inband_ip=dict(required=False, type='str',
                              default='172.16.0.0/24'),
            pn_fabric_control_network=dict(required=False, type='str',
                                           choices=['mgmt', 'in-band'],
                                           default='mgmt'),
            pn_bgp_as_range=dict(required=False, type='str', default='65000'),
            pn_bgp_redistribute=dict(required=False, type='str',
                                     choices=['none', 'static', 'connected',
                                              'rip', 'ospf'],
                                     default='connected'),
            pn_bgp_maxpath=dict(required=False, type='str', default='16'),
        )
    )

    bgp_as_range = module.params['pn_bgp_as_range']
    bgp_redistribute = module.params['pn_bgp_redistribute']
    bgp_maxpath = module.params['pn_bgp_maxpath']
    message = ' '
    message += assign_bgp_as(module, bgp_as_range)
    message += ' bgp_as assigned '
    message += assign_bgp_redistribute(module, bgp_redistribute)
    message += ' '
    message += assign_bgp_maxpath(module, bgp_maxpath)
    message += ' '
    message += bgp_neighbor(module)
    message += ' '
    message += assign_router_id(module)
    message += ' '
    message += create_leaf_cluster(module)
    message += ' '

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

