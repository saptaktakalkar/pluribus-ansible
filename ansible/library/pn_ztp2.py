import shlex
import json

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
        cli = '/usr/bin/cli --quiet --user %s:%s'  % (username, password)
    else:
        cli = '/usr/bin/cli --quiet '

    if cliswitch:
        cli += ' switch ' + cliswitch
    #else:
    #    cli += ' switch-local '

    return cli


def run_cli(module, cli):
    """
    This method executes the cli command on the target node(s) and returns the
    output.
    :param module: The Ansible module to fetch input parameters.
    :param cli: the complete cli string to be executed on the target node(s).
    :return: Output/Error or Success message depending upon the response from cli.
    """

    cli = shlex.split(cli)
    rc, out, err = module.run_command(cli)
#    print "rc",rc
#    print "out",out
#    print "err",err
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






def bgp_as(module,bgp_as):
    output = ' '
#    loopback_address = module.params['pn_loopback_ip']
    bgp_as_spine = bgp_as
    bgp_leaf = int(bgp_as) + 1
    leaf_list = module.params['pn_leaf_list']
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
                cli += ' vrouter-show name %s format location no-show-headers ' % (vrouter)
                switch_vrouter = run_cli(module,cli).split()
                if switch_vrouter[0] in spine_list:
                    cli = clicopy
                    cli += ' vrouter-modify name %s bgp-as %s ' % (vrouter, bgp_as_spine)
                    output += run_cli(module,cli)
                    output += ' '

                else:
                    cli = clicopy
                    cli += ' vrouter-modify name %s bgp-as %s ' % (vrouter, str(bgp_leaf))
                    output += run_cli(module,cli)
                    output += ' '
                    bgp_leaf += 1
    
    else:
        output += "no vrouters present"

    return output





def bgp_neighbor(module):
    
    output = ' '
    cli = pn_cli(module)
    if 'switch' in cli:
        cli = cli.rpartition('switch')[0]
    clicopy = cli
    cli += ' vrouter-show format name no-show-headers '
    vrouter_names = run_cli(module, cli).split()
#    vrouter_names = ['o-spine1-vrouter']
    if len(vrouter_names) > 0:
        for vrouter in vrouter_names:

            cli = clicopy
            cli += ' vrouter-show name %s format location no-show-headers ' % (vrouter)
            switch = run_cli(module, cli).split()


            cli = clicopy
            cli += ' vrouter-interface-show vrouter-name %s format l3-port no-show-headers ' % (vrouter)
            port_num = run_cli(module, cli).split()
            port_num = list(set(port_num))
            port_num.remove(vrouter)
          
            

                #cli = clicopy
                #cli += ' switch %s port-show port %s format rport no-show-headers ' % (leaf, lport)

                #sport = run_cli(module, cli)




            for port in port_num:
                   

 
                cli = clicopy
                cli += ' switch %s port-show port %s format hostname no-show-headers ' % (switch[0], port)               # use port in pl;ace of static port number
                hostname = run_cli(module, cli).split()
               
                cli = clicopy
                cli += ' vrouter-show location %s format bgp-as no-show-headers ' % (hostname[0])    
                bgp_hostname = run_cli(module, cli).split()
        
                #cli = clicopy
                #cli += ' switch %s port-show hostname %s format port no-show-headers ' % (hostname[0], switch[0])
                #port_hostname = run_cli(module, cli).split()

                cli = clicopy
                cli += ' switch %s port-show port %s format rport no-show-headers ' % (switch[0], port)

                port_hostname = run_cli(module, cli)

        
                cli = clicopy
                cli += ' vrouter-show location %s format name no-show-headers ' % (hostname[0])
                vrouter_hostname = run_cli(module,cli).split()
        
                cli = clicopy
                cli += ' vrouter-interface-show vrouter-name %s l3-port %s format ip no-show-headers ' % (vrouter_hostname[0], port_hostname)
                ip_hostname_subnet = run_cli(module, cli).split()
                ip_hostname_subnet.remove(vrouter_hostname[0])
         
                ip_hostname_subnet = ip_hostname_subnet[0].split('/')
                ip_hostname = ip_hostname_subnet[0]
        
                cli = clicopy
                cli += ' vrouter-bgp-show remote-as %s neighbor %s format switch no-show-headers ' %(bgp_hostname[0], ip_hostname)
                already_added = run_cli(module,cli).split()
                if vrouter in already_added:
                    output += " already exists bgp in %s " % (vrouter)
                    output += ' '
                else:
                    cli = clicopy
                    cli += ' vrouter-bgp-add vrouter-name %s neighbor %s remote-as %s ' % (vrouter, ip_hostname, bgp_hostname[0])
                    output += run_cli(module,cli)
                    output += ' added bgp %s ' % (vrouter)     
    else:
        print "no vrouter created yet"
    return output


def assign_router_id(module):
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
            cli += ' vrouter-loopback-interface-show vrouter-name %s format ip no-show-headers ' % (vrouter)
            loopback_ip = run_cli(module, cli).split()
            loopback_ip.remove(vrouter)
            
            cli = clicopy
            cli += ' vrouter-modify name %s router-id %s ' % (vrouter,loopback_ip[0])
            output += run_cli(module, cli)
            output += ' '

    else:
        print "No vrouters"
    return output        






def bgp_redistribute_maxpath(module):
    bgp_redistribute = module.params['pn_bgp_redistribute']
    bgp_maxpath = module.params['pn_bgp_maxpath']   
    output = ' '
    cli = pn_cli(module)
    if 'switch' in cli:
        cli = cli.rpartition('switch')[0]
    clicopy = cli
    
    cli += ' vrouter-show format name no-show-headers '
    vrouter_names = run_cli(module, cli).split()

    for vrouter in vrouter_names:
        cli = clicopy
        cli += ' vrouter-modify name %s bgp-redistribute %s ' % (vrouter,bgp_redistribute)
        output += run_cli(module,cli)
        output += ' '
        cli = clicopy
        cli += ' vrouter-modify name %s bgp-max-paths %s ' % (vrouter,bgp_maxpath)
        output += run_cli(module,cli)        
        output += ' '
    return output   


def leaf_no_cluster(module, leaf_list):
    cli = pn_cli(module)
    noncluster_leaf = []
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
            noncluster_leaf.append(leaf)

    return noncluster_leaf


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
    cli += ' switch %s cluster-show format name no-show-headers ' % (node1)
    cluster_list = run_cli(module, cli).split()
    if name not in cluster_list:
        cli = clicopy
        cli += ' switch %s cluster-create name %s ' % (switch, name)
        cli += ' cluster-node-1 %s cluster-node-2 %s ' % (node1, node2)
        return run_cli(module, cli)
    else:
        return "Already part of a cluster"




def leaf_cluster_formation(module, noncluster_leaf, spine_list):


    cli = pn_cli(module)
    if 'switch' in cli:
        cli = cli.rpartition('switch')[0]
    clicopy = cli

    output = ' '

    flag = 0
    while flag == 0:
        if len(noncluster_leaf) == 0:
            output += "no more leaf to create cluster"
            output += ' '
            flag += 1
        else:
            node1 = noncluster_leaf[0]
            noncluster_leaf.remove(node1)
            cli = clicopy
            cli += ' switch %s lldp-show format sys-name no-show-headers ' % node1
            system_names = run_cli(module, cli).split()
            system_names = list(set(system_names))

            flag1 = 0
            i = 0
            while (i < len(system_names)) and (flag1 == 0):
                switch = system_names[i]
                if switch not in spine_list:
                    if switch in noncluster_leaf:
                        name = node1 + '-to-' + switch + '-cluster'
                        output += create_cluster(module, switch, name, node1, switch)
                        output += ' '
                        noncluster_leaf.remove(switch)
                        flag1 += 1
                    else:
                        print "switch already has a cluster"
                else:
                    print "switch is a spine"

                i += 1
    return output







def create_leaf_cluster(module):

    output = ' '

    spine_list = module.params['pn_spine_list']
    leaf_list = module.params['pn_leaf_list']

    noncluster_leaf = leaf_no_cluster(module, leaf_list)

    output += leaf_cluster_formation(module, noncluster_leaf, spine_list)
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
            pn_fabric_retry=dict(required=False, type='int' ,default=1),
            pn_run_l2_l3=dict(required=False, type='bool', default=False),
            pn_net_address=dict(required=False, type='str'),
            pn_cidr=dict(required=False, type='str'),
            pn_supernet=dict(required=False, type='str'),
            pn_spine_list=dict(required=False, type='list'),
            pn_leaf_list=dict(required=False, type='list'),
            pn_update_fabricto_inband=dict(required=False, type='bool', default=False),
            pn_assign_loopback=dict(required=False, type='bool', default=False),
            pn_loopback_ip=dict(required=False, type='str', default='101.101.101.0/32'),
            pn_inband_ip=dict(required=False, type='str', default='172.16.0.0/24'),
            pn_fabric_control_network=dict(required=False, type='str',choices=['mgmt', 'in-band'],default='mgmt'),
            pn_bgp_as_range=dict(required=False, type='str', default='65000'),
            pn_bgp_redistribute = dict(required=False, type='str',
                                       choices=['none','static','connected', 'rip', 'ospf'],
                                        default='connected'),
            pn_bgp_maxpath = dict(required=False, type='str', default='16')
        )
    )

    fabric_name = module.params['pn_fabric_name']
    fabric_network = module.params['pn_fabric_network']
    fabric_type = module.params['pn_fabric_type']
    run_l2_l3 = module.params['pn_run_l2_l3']
    control_network = module.params['pn_fabric_control_network']
    update_fabricto_inband = module.params['pn_update_fabricto_inband']
 #   inband_address = module.params['pn_inband_ip']
    bgp_as_range = module.params['pn_bgp_as_range']
    message = ' '



    message += ' '
    message += bgp_as(module,bgp_as_range)
    message += ' bgp_as assigned '
    message += bgp_redistribute_maxpath(module)
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

 
