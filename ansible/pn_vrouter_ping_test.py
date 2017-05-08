#!/usr/bin/python

# PYTHON SCRIPT FOR VROUTER PING TEST

# The ip includes(for ping test): all the l3-port ips, vips and master ips
# The results are shown in the cli
# Detailed ping report is stored in the file named ping_python.txt formed in the same folder

# ---- RUN COMMAND ----
# Following command can be used to run this script:
# python <python_script_name>
# eg: python pn_vrouter_ping_test.py

import subprocess
import time

def pn_cli():
    """
    This method is to generate the cli portion to launch the Netvisor cli.
    It parses the username, password, switch parameters from module.
    :return: The cli string for further processing.
    """
    username = 'network-admin'
    password = 'test123'

    if username and password:
        cli = '/usr/bin/cli --quiet --user %s:%s ' % (username, password)
    else:
        cli = '/usr/bin/cli --quiet '

    return cli


def vrouter_ping_test():
    """
    This method is used to find out all the assigned(excluding slave vrrp ips) ips
    and do a vrouter-ping test to check the connectivity from all vrouters to
    these ips.
    :return: It returns a 'script complete' message at the end of the run.
    """
    vrrp_flag = 0
    vrouter_ip_list = []
    f1 = open('ping_python.txt', 'w')
    cli = pn_cli()
    clicopy = cli

    cli += ' vrouter-show format name no-show-headers '
    vrouter_list = subprocess.check_output(cli, shell=True).split()

    cli = clicopy
    cli += ' vrouter-interface-show vrrp-state master format ip no-show-headers '
    vrrp_ip_list = subprocess.check_output(cli, shell=True).split()
    vrrp_ip_list = list(set(vrrp_ip_list))
    if len(vrrp_ip_list) > 0 and 'Success' not in vrrp_ip_list:
        vrrp_flag = 1

    for vrouter in vrouter_list:
        if vrrp_flag == 1 and vrouter in vrrp_ip_list:
            vrrp_ip_list.remove(vrouter)

        cli = clicopy
        cli += ' vrouter-interface-show vrouter-name %s format l3-port no-show-headers ' % vrouter
        port_list = subprocess.check_output(cli, shell=True).split()
        port_list = list(set(port_list))
        port_list.remove(vrouter)

        for port in port_list:
            cli = clicopy
            cli += ' vrouter-interface-show vrouter-name %s l3-port %s format ip no-show-headers ' % (vrouter, port)
            ip = subprocess.check_output(cli, shell=True).split()
            ip = list(set(ip))
            ip.remove(vrouter)
            vrouter_ip_list.append(ip[0])

    if vrrp_flag == 1:
        for vrrp_ip in vrrp_ip_list:
            vrouter_ip_list.append(vrrp_ip)
            vrrp_ip = vrrp_ip.split('.')
            master_vrrp_ip = vrrp_ip[0] + '.' + vrrp_ip[1] + '.' + vrrp_ip[2] + '.'
            master_vrrp_ip += '2'
            vrouter_ip_list.append(master_vrrp_ip)

    f1.write('%s \n' % vrouter_ip_list)

    for vrouter in vrouter_list:
        for ip in vrouter_ip_list:
            ip = ip.split('/')[0]

            cli = clicopy
            cli += 'vrouter-ping vrouter-name %s host-ip %s count 1' % (vrouter, ip)
            message = subprocess.check_output(cli, shell=True)
            f1.write('\n\n %s \n' % message)

            if 'unreachable' in message or 'Unreachable' in message or '100% packet loss' in message:
                print ' Failed! %s: vrouter-ping failed from vrouter %s to ip %s \n' % (vrouter, vrouter, ip)
                f1.write(' Failed! %s: vrouter-ping failed from vrouter %s to ip %s \n' % (vrouter, vrouter, ip))
            else:
                print ' Success! %s: vrouter-ping successful from vrouter %s to ip %s \n' % (vrouter, vrouter, ip)
                f1.write(' Success! %s: vrouter-ping successful from vrouter %s to ip %s \n' % (vrouter, vrouter, ip))

            time.sleep(1)

    f1.close()
    return 'Script complete'


message = vrouter_ping_test()
print message

