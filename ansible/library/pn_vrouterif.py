#!/usr/bin/python
""" PN-CLI vrouter-interface-add/remove """

import subprocess
import shlex
import re

DOCUMENTATION = """
---
module: pn_vrouterif
author: "Pluribus Networks"
short_description: CLI command to add/remove vrouter-interface.
description:
  - Execute vrouter-interface-add, vrouter-interface-remove
    command.
  - You can configure interfaces to vRouter services on a fabric,
    cluster, standalone switch or virtual network(VNET).
options:
  pn_cliusername:
    description:
      - Login username.
    required: true
    type: str
  pn_clipassword:
    description:
      - Login password.
    required: true
    type: str
  pn_cliswitch:
    description:
    - Target switch to run the cli on.
    required: False
    type: str
  pn_command:
    description:
      - The C(pn_command) takes the vrouter-interface command as value.
    required: true
    choices: ['vrouter-interface-add', 'vrouter-interface-remove']
    type: str
  pn_vrouter_name:
    description:
      - Specify the name of the vRouter interface.
    required: true
    type: str
  pn_vlan:
    description:
      - Specify the VLAN identifier. This is a value between 1 and
        4092.
    type: int
  pn_interface_ip:
    description:
      - Specify the IP address of the interface.
      - For VRRP interface, specify the IP in pn_vrrp_ip. Specify the IP of the
        primary interface here.
    type: str
  pn_netmask:
    description:
      - Specify the netmask.
    type: str
  pn_assignment:
    description:
      - Specify the DHCP method for IP address assignment.
      - Choices- none, dhcp, dhcpv6, autov6
    type: str
  pn_vxlan:
    description:
      - Specify the VXLAN identifier. This is a value between 1 and 16777215.
    type: str
  pn_interface:
    description:
      - Specify if the interface is management, data or span interface.
      - Choices- mgmt, data, span.
    type: str
  pn_alias:
    description:
      - Specify an alias for the interface.
    type: str
  pn_exclusive:
    description:
      - Specify if the interface is exclusive to the configuration. Exclusive
        means that other configurations cannot use the interface. Exclusive is
        specified when you configure the interface as span interface and allows
        higher throughput through the interface.
    type: bool
  pn_nic_enable:
    description:
      - Specify if the NIC is enabled or not
    type: bool
  pn_vrrpid:
    description:
      - Specify the ID for the VRRP interface. The IDs on both vRouters must be
        the same IS number.
    type: int
  pn_vrrp_ip:
    description:
      - Specify the IP for VRRP interface.
    type: str
  pn_vrrp_priority:
    description:
      - Speicfies the priority for the VRRP interface. This is a value between
         1 (lowest) and 255 (highest).
    type: int
  pn_vrrp_adv_int:
    description:
      - Specify a VRRP advertisement interval in milliseconds. The range is
        from 30 to 40950 with a default value of 1000.
    type: str
  pn_l3port:
    description:
      - Specify a Layer 3 port for the interface.
    type: str
  pn_secondary_macs:
    description:
      - Specify a secondary MAC address for the interface.
    type: str
  pn_nic_str:
    description:
      - Specify the type of NIC. Used for vrouter-interface remove/modify.
    type: str
  pn_quiet:
    description:
      - The C(pn_quiet) option to enable or disable the system bootup message
    required: false
    type: bool
    default: true
"""

EXAMPLES = """
- name: Add vrouter-interface
  pn_vrouterif:
    pn_cliusername: admin
    pn_clipassword: admin
    pn_command: 'vrouter-interface-add'
    pn_vrouter_name: 'ansible-vrouter'
    pn_interface_ip: 101.101.101.2/24
    pn_vlan: 101

- name: Add VRRP...
  pn_vrouterif:
    pn_cliusername: admin
    pn_clipassword: admin
    pn_command: vrouter-interface-add
    pn_vrouter_name: 'ansible-vrouter'
    pn_interface_ip: 101.101.101.2/24
    pn_vrrp_ip: 101.101.101.1/24
    pn_vrrp_priority: 100
    pn_vlan: 101

- name: Remove vrouter-interface
  pn_vrouterif:
    pn_cliusername: admin
    pn_clipassword: admin
    pn_command: 'vrouter-interface-remove'
    pn_vrouter_name: 'ansible-vrouter'
    pn_interface_ip: 101.101.101.2/24
"""

RETURN = """
command:
  description: the CLI command run on the target node(s).
stdout:
  description: the set of responses from the vrouterif command.
  returned: always
  type: list
stderr:
  description: the set of error responses from the vrouterif command.
  returned: on error
  type: list
changed:
  description: Indicates whether the CLI caused changes on the target.
  returned: always
  type: bool
"""


def main():
    """ This portion is for arguments parsing """
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=True, type='str'),
            pn_clipassword=dict(required=True, type='str'),
            pn_cliswitch=dict(required=False, type='str'),
            pn_command=dict(required=True, type='str',
                            choices=['vrouter-interface-add',
                                     'vrouter-interface-remove']),
            pn_vrouter_name=dict(required=True, type='str'),
            pn_vlan=dict(type='int'),
            pn_interface_ip=dict(type='str'),
            pn_vrrp_ip=dict(type='str'),
            pn_netmask=dict(type='str'),
            pn_assignment=dict(type='str',
                               choices=['none', 'dhcp', 'dhcpv6', 'autov6']),
            pn_vxlan=dict(type='str'),
            pn_interface=dict(type='str', choices=['mgmt', 'data', 'span']),
            pn_alias=dict(type='str'),
            pn_exclusive=dict(type='bool'),
            pn_nic_enable=dict(type='bool'),
            pn_vrrp_id=dict(type='int'),
            pn_vrrp_priority=dict(type='int'),
            pn_vrrp_adv_int=dict(type='str'),
            pn_l3port=dict(type='str'),
            pn_secondary_macs=dict(type='str'),
            pn_nic_str=dict(type='str'),
            pn_quiet=dict(default=True, type='bool')
        ),
        required_if=(
            ["pn_command", "vrouter-interface-add",
             ["pn_vrouter_name", "pn_interface_ip"]],
            ["pn_command", "vrouter-interface-remove",
             ["pn_vrouter_name", "pn_nic_str"]]
        ),
    )

    cliusername = module.params['pn_cliusername']
    clipassword = module.params['pn_clipassword']
    cliswitch = module.params['pn_cliswitch']
    command = module.params['pn_command']
    vrouter_name = module.params['pn_vrouter_name']
    vlan = module.params['pn_vlan']
    interface_ip = module.params['pn_interface_ip']
    netmask = module.params['pn_netmask']
    assignment = module.params['pn_assignment']
    vxlan = module.params['pn_vxlan']
    interface = module.params['pn_interface']
    alias = module.params['pn_alias']
    exclusive = module.params['pn_exclusive']
    nic_enable = module.params['pn_nic_enable']
    vrrp_id = module.params['pn_vrrp_id']
    vrrp_ip = module.params['pn_vrrp_ip']
    vrrp_priority = module.params['pn_vrrp_priority']
    vrrp_adv_int = module.params['pn_vrrp_adv_int']
    l3port = module.params['pn_l3port']
    secondary_macs = module.params['pn_secondary_macs']
    nic_str = module.params['pn_nic_str']
    quiet = module.params['pn_quiet']

    # Building the CLI command string
    if quiet is True:
        cli = ('/usr/bin/cli --quiet --user ' + cliusername + ':' +
               clipassword)
    else:
        cli = '/usr/bin/cli --user ' + cliusername + ':' + clipassword

    if cliswitch:
        if cliswitch == 'local':
            cli += ' switch-local '
        else:
            cli += ' switch ' + cliswitch

    cli += ' ' + command + ' vrouter-name ' + vrouter_name


    if command == 'vrouter-interface-add':

        if vrrp_ip:

            show_cmd = ('/usr/bin/cli --quiet --user ' + cliusername + ':' +
                        clipassword + ' vrouter-interface-show vrouter-name ' +
                        vrouter_name + ' ip ' + vrrp_ip + ' vrrp-id ' + str(vrrp_id))

            show_cmd = shlex.split(show_cmd)
            result = subprocess.Popen(show_cmd, stderr=subprocess.PIPE,
                                      stdout=subprocess.PIPE, universal_newlines=True)
            out, err = result.communicate()
            if out:
                module.exit_json(changed=False, msg="Interface already in use")
            if err:
                module.exit_json(changed=False, stderr=err.rstrip("\r\n"))

            show_cmd = ('/usr/bin/cli --quiet --user ' + cliusername + ':' +
                        clipassword + ' vrouter-interface-show vrouter-name ' +
                        vrouter_name + ' ip ' + interface_ip +
                        ' format nic no-show-headers parsable-delim % ')

            show_cmd = shlex.split(show_cmd)
            result = subprocess.Popen(show_cmd, stderr=subprocess.PIPE,
                                      stdout=subprocess.PIPE, universal_newlines=True)
            out, err = result.communicate()

            if err:
                module.exit_json(changed=False, stderr=err.rstrip("\r\n"))

            if out:
                show = out.rstrip("\r\n")
                vrouter, vrrp_nic = show.split('%')

            cli += ' ip ' + vrrp_ip

            if vrrp_id:
                cli += ' vrrp-id ' + str(vrrp_id)

            cli += ' vrrp-primary ' + vrrp_nic

            if vrrp_priority:
                cli += ' vrrp-priority ' + str(vrrp_priority)

            if vrrp_adv_int:
                cli += ' vrrp-adv-int ' + vrrp_adv_int

        else:
            cli += ' ip ' + interface_ip

        if vlan:
            cli += ' vlan ' + str(vlan)

        if l3port:
            cli += ' l3-port ' + l3port

        if netmask:
            cli += ' netmask ' + netmask

        if assignment:
            cli += ' assignment ' + assignment

        if vxlan:
            cli += ' vxlan ' + vxlan

        if interface:
            cli += ' if ' + interface

        if alias:
            cli += ' alias-on ' + alias

        if exclusive is True:
            cli += ' exclusive '
        if exclusive is False:
            cli += ' no-exclusive '

        if nic_enable is True:
            cli += ' nic-enable '
        if nic_enable is False:
            cli += ' nic-disable '

        if secondary_macs:
            cli += ' secondary-macs ' + secondary_macs

    if command == 'vrouter-interface-remove':

        cli += ' nic ' + nic_str


    # Run the CLI command
    vrouterifcmd = shlex.split(cli)
    response = subprocess.Popen(vrouterifcmd, stderr=subprocess.PIPE,
                                stdout=subprocess.PIPE, universal_newlines=True)

    # 'out' contains the output
    # 'err' contains the err messages
    out, err = response.communicate()

    exp = re.compile(r'.*(eth\d*.\d*).*')
    nic = exp.findall(out)

    # Response in JSON format
    if err:
        module.exit_json(
            command=cli,
            stderr=err.rstrip("\r\n"),
            changed=False
        )

    else:
        module.exit_json(
            command=cli,
            stdout=out.rstrip("\r\n"),
            nic=nic,
            changed=True
        )

# Ansible boiler-plate
from ansible.module_utils.basic import AnsibleModule

if __name__ == '__main__':
    main()

