import shlex

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


def auto_accept_eula(module):
    """
    Method to accept the EULA when we first login to a new switch.
    :param module: The Ansible module to fetch input parameters.
    :return: The output of run_cli() method.
    """
    password = module.params['pn_clipassword']
    cli = ' /usr/bin/cli --quiet --skip-setup eula-show '
    cli = shlex.split(cli)
    rc, out, err = module.run_command(cli)

    if err:
        cli = '/usr/bin/cli --quiet'
        cli += ' --skip-setup --script-password '
        cli += ' switch-setup-modify password ' + password
        cli += ' eula-accepted true '
        return run_cli(module, cli)
    elif out:
        return ' EULA has been accepted already! '




def assign_inband_ip(module, inband_ip):
    """
    Method to assign in-band ips to switches.
    :param module: The Ansible module to fetch input parameters.
    :param inband_address: The network ip for the in-band ips.
    :return: The output messages for assignment.
    """
    supernet = 4
    spine_list = module.params['pn_spine_list']
    leaf_list = module.params['pn_leaf_list']
    current_switch = module.params['pn_current_switch']
    output = ''
    if current_switch in spine_list:
        spine_pos = int(spine_list.index(current_switch))
        ip_count = (supernet * spine_pos) + 1

    elif current_switch in leaf_list:
        spine_count = len(spine_list)
        leaf_pos = int(leaf_list.index(current_switch))
        ip_count = (supernet * leaf_pos) + 1
        ip_count += (int(spine_count) * supernet)
        
    address = inband_ip.split('.')
    static_part = str(address[0]) + '.' + str(address[1]) + '.'
    static_part += str(address[2]) + '.'
    last_octet = str(address[3]).split('/')
    subnet = last_octet[1]

    cli = pn_cli(module)
    clicopy = cli

    ip = static_part + str(ip_count) + '/' + str(30)
    
    cli = clicopy
    cli += 'switch-setup-modify in-band-ip %s ' % ip
    output += run_cli(module, cli)

    return output


def fabric_conn(module, ip1, ip2):
    output = ''
    supernet = 4
    vrouter_name =  module.params['pn_current_switch']
    bgp_spine = module.params['pn_bgp_as_range']
    spine_list = module.params['pn_spine_list']
    leaf_list = module.params['pn_leaf_list']
    current_switch = module.params['pn_current_switch']

    cli = pn_cli(module)
    clicopy = cli

    cli = clicopy
    cli += 'switch-setup-show format in-band-ip no-show-headers'
    inband_ip = run_cli(module, cli)
    address = inband_ip.split(':')[1]
    address = address.replace(' ','')
    address = address.split('.')
    static_part = str(address[0]) + '.' + str(address[1]) + '.'
    static_part += str(address[2]) + '.'
    last_octet = str(address[3]).split('/')
    netmask = last_octet[1]
    gateway_ip = int(last_octet[0]) + 1
    ip = static_part + str(gateway_ip)

    spine_count = len(spine_list)

    #remote-as for leaf is always spine1 and for spine is always leaf1
    if current_switch in spine_list:
        bgp_as = bgp_spine
        remote_as = str(int(bgp_spine) + 1)

        cli = clicopy
        cli += 'port-show hostname %s format port, no-show-headers' % leaf_list[0]
        ports = run_cli(module, cli).split()

        cli = clicopy
        cli += 'trunk-show ports %s format trunk-id, no-show-headers ' % ports[0]
        trunk_id = run_cli(module, cli)
        if len(trunk_id) == 0 or trunk_id == 'Success':
            l3_port = ports[0]
        else:
            l3_port = trunk_id

        fabric_network_addr = static_part + str(supernet * spine_count) + '/' + netmask


    else:
        switch_pos = int(leaf_list.index(current_switch)) + 1
        bgp_as = str(int(bgp_spine) + switch_pos)
        remote_as = bgp_spine

        cli = clicopy
        cli += 'port-show hostname %s format port, no-show-headers' % spine_list[0]
        ports = run_cli(module, cli).split()

        cli = clicopy
        cli += 'trunk-show ports %s format trunk-id, no-show-headers ' % ports[0]
        trunk_id = run_cli(module, cli)
        if len(trunk_id) == 0 or trunk_id == 'Success':
            l3_port = ports[0]
        else:
            l3_port = trunk_id

        fabric_network_addr = static_part + str(0) + '/' + netmask

    cli = clicopy
    cli += 'fabric-comm-vrouter-bgp-create name %s bgp-as %s' % (vrouter_name, bgp_as) 
    cli += ' bgp-nic-ip %s bgp-nic-l3-port %s' % (ip1, l3_port)
    cli += ' neighbor %s remote-as %s ' % (ip2, remote_as) 
    cli += ' fabric-network %s in-band-nic-ip %s in-band-nic-netmask %s' % (fabric_network_addr, ip, netmask)

    output += run_cli(module, cli) 
    return output


def configure_fabric_over_l3(module):
    supernet = 4
    output = ''
    inband_ip = module.params['pn_inband_ip']
    bgp_ip = module.params['pn_bgp_ip']
    spine_list = module.params['pn_spine_list']
    leaf_list = module.params['pn_leaf_list']
    current_switch = module.params['pn_current_switch']
    
    output += assign_inband_ip(module, inband_ip)

    address = bgp_ip.split('.')
    static_part = str(address[0]) + '.' + str(address[1]) + '.'
    static_part += str(address[2]) + '.'
    last_octet = str(address[3]).split('/')
    subnet = last_octet[1]
    leaf_count = len(leaf_list)
    spine_count = len(spine_list)

    if current_switch in spine_list:
        for leaf in leaf_list:
            if leaf_list.index(leaf) == 0:
                spine_pos = spine_list.index(current_switch)
                ip1_count = (spine_pos * leaf_count * supernet) + 1
                ip2_count = (spine_pos * leaf_count * supernet) + 2
                ip1 = static_part + str(ip1_count) + '/' + str(30)
                ip2 = static_part + str(ip2_count)
                output += fabric_conn(module, ip1, ip2)
            else:
                pass

    elif current_switch in leaf_list:
        for spine in spine_list:
            if spine_list.index(spine) == 0:
                leaf_pos = leaf_list.index(current_switch)
                ip1_count = (leaf_pos * supernet) + 2
                ip2_count = (leaf_pos * supernet) + 1
                ip1 = static_part + str(ip1_count) + '/' + str(30)
                ip2 = static_part + str(ip2_count)
                output += fabric_conn(module, ip1, ip2)
            else:
                pass    
    


    return output




def main():
    """ This section is for arguments parsing """
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=False, type='str'),
            pn_clipassword=dict(required=False, type='str', no_log=True),
            pn_fabric_name=dict(required=True, type='str'),
            pn_fabric_network=dict(required=False, type='str',
                                   choices=['mgmt', 'in-band'],
                                   default='mgmt'),
            pn_fabric_type=dict(required=False, type='str',
                                choices=['layer2', 'layer3'],
                                default='layer2'),
            pn_run_l2_l3=dict(required=False, type='bool', default=False),
            pn_net_address=dict(required=False, type='str'),
            pn_cidr=dict(required=False, type='str'),
            pn_supernet=dict(required=False, type='str'),
            pn_spine_list=dict(required=False, type='list'),
            pn_leaf_list=dict(required=False, type='list'),
            pn_update_fabric_to_inband=dict(required=False, type='bool',
                                            default=False),
            pn_assign_loopback=dict(required=False, type='bool', default=False),
            pn_loopback_ip=dict(required=False, type='str',
                                default='109.109.109.0/24'),
            pn_inband_ip=dict(required=False, type='str',
                              default='172.16.0.0/24'),
            pn_fabric_control_network=dict(required=False, type='str',
                                           choices=['mgmt', 'in-band'],
                                           default='mgmt'),
            pn_toggle_40g=dict(required=False, type='bool', default=True),
            pn_current_switch=dict(required=False, type='str'),
            pn_bgp_as_range=dict(required=False, type='str', default='65000'),
            pn_bgp_ip=dict(required=False, type='str', default='100.1.1.0/24'),
        )
    )

    fabric_name = module.params['pn_fabric_name']
    inband_ip = module.params['pn_inband_ip']
    current_switch = module.params['pn_current_switch']
    message = ' '

    #eula_out_msg = auto_accept_eula(module)
    message += configure_fabric_over_l3(module)
    







    module.exit_json(
        stdout=message,
        error='0',
        failed=False,
        changed=True
    )


# AnsibleModule boilerplate
from ansible.module_utils.basic import AnsibleModule

if __name__ == '__main__':
    main()

