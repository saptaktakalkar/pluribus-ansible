#!/usr/bin/python
""" PN CLI vflow-create/vflow-delete/vflow-modify """

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
module: pn_vflow
author: "Pluribus Networks (devops@pluribusnetworks.com)"
version: 1.0
short_description: CLI command to create/delete/modify a vFlow.
description:
  - Execute vflow-create or vflow-delete or vflow-modify command.
  - vFlow is a virtual filter/rule which is created to manage switch traffic by
    assigning different actions that matches given criteria/qualifiers.
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
  pn_cliswitch:
    description:
      - Target switch(es) to run the cli on.
    required: False
    type: str0
  pn_command:
    description:
      - The C(pn_command) takes the vFlow commands as value.
    required: true
    choices: ['vflow-create', 'vflow-delete', 'vflow-modify']
    type: str
  pn_name:
    description:
      - Specify the name for the vFlow configuration.
    required: true
    type: str
  pn_scope:
    description:
      - Specify the scope of a vFlow.
    choices: ['local', 'fabric']
    type: str
  pn_vnet:
    description:
      - Specify the vnet assigned to the vFlow.
    type: str
  pn_vlan:
    description
      - Specify the vlan for the vFlow.
    type: str
  pn_in_port:
    description:
      - Specify incoming port list for the vFlow.
    type: str
  pn_out_port:
    description:
      - Specify outgoing port list for the vFlow.
    type: str
  pn_ether_type:
    description:
      - Specify the ether type for the vFlow.
    choices: ['ipv4', 'arp', 'wake', 'rarp', 'vlan' ,'ipv6', 'mpls-uni', 'mpls-
    multi', 'jumbo', 'aoe', 'dot1X', 'lldp', 'ecp', 'macsec', 'ptp', 'fcoe',
    'fcoe-init', 'qinq']
    type: str
  pn_src_mac:
    description
      - Specify source MAC address for the vFlow.
    type: str
  pn_src_mac_mask:
    description
      - Specify source MAC address to use as a wildcard mask for the vFlow.
    type: str
  pn_dst_mac:
    description
      - Specify destination MAC address for the vFlow.
    type: str
  pn_dst_mac_mask:
    description
      - Specify destination MAC address to use as a wildcard mask for the vFlow.
    type: str
  pn_src_ip:
    description
      - Specify source IP address for the vFlow.
    type: str
  pn_src_ip_mask:
    description
      - Specify source IP address wildcard mask for the vFlow.
    type: str
  pn_dst_ip:
    description
      - Specify destination IP address for the vFlow.
    type: str
  pn_dst_ip_mask:
    description
      - Specify destination IP address wildcard mask for the vFlow.
    type: str
  pn_src_port:
    description
      - Specify Layer 3 source port for the vFlow.
    type: str
  pn_src_port_mask:
    description
      - Specify source port mask for the vFlow.
    type: str
  pn_dst_port:
    description
      - Specify Layer 3 destination port for the vFlow.
    type: str
  pn_dst_port_mask:
    description
      - Specify destination port mask for the vFlow.
    type: str
  pn_dscp_start:
    description
      - Specify 6-bit Differentiated Services Code Point (DSCP) start number.
    type: str
  pn_dscp_end:
    description
      - Specify 6-bit Differentiated Services Code Point (DSCP) end number.
    type: str
  pn_dscp:
    description
      - Specify 6-bit Differentiated Services Code Point (DSCP) for the vFlow
        with range 0 to 63.
    type: str
  pn_tos_start:
    description
      - Specify start Type of Service (ToS) number.
    type: str
  pn_tos_end:
    description
      - Specify ending Type of Service (ToS) number.
    type: str
  pn_tos:
    description
      - Specify ToS number for the vFlow.
    type: str
  pn_vlan_pri:
    description
      - Specify priority for the VLAN - 0 to 7.
    type: str
  pn_ttl:
    description
      - Specify time to live.
    type: str
  pn_proto:
    description
      - Specify layer 3 protocol for the vFlow.
    choices: ['tcp', 'udp', 'icmp', 'igmp', 'ip']
    type: str
  pn_flow_class:
    description
      - Specify vFlow class name.
    type: str
  pn_ingress_tunnel:
    description
      - Specify tunnel for the ingress traffic.
    type: str
  pn_egress_tunnel:
    description
      - Specify tunnel for the egress traffic.
    type: str
  pn_bw_min:
    description
      - Specify the minimum bandwidth in Gbps.
    type: str
  pn_bw_max:
    description
      - Specify the maximum bandwidth in Gbps.
    type: str
  pn_precedence:
    description
      - Specify the traffic priority value between 2 and 15.
    type: str
  pn_action:
    description
      - Specify forwarding action to apply to the vFlow.
    choices: ['none', 'drop', 'to-port', 'to-cpu', 'trap', 'copy-to-cpu',
    'copy-to-port', 'check', 'setvlan', 'tunnel-pkt', 'set-tunnel-id',
    'to-span', 'cpu-rx', 'cpu-rx-tx', 'set-metadata', 'set-dscp', 'decap',
    'set-dmac', 'set-dmac-to-port', 'to-ports-and-cpu', 'set-vlan-pri',
    'tcp-seq-offset', 'tcp-ack-offset', 'l3-to-cpu-switch']
    type: str
  pn_action_value:
    description
      - Specify optional value argument between 1 and 64.
    type: str
  pn_action_set_mac_value:
    description
      - Specify MAC address value.
    type: str
  pn_action_to_ports_value:
    description
      - Specify action to port value.
    type: str
  pn_mirror:
    description
      - Specify mirror configuration name.
    type: str
  pn_process_mirror:
    description
      - Specify vFLow processes mirrored traffic or not.
    choices: ['process-mirror', 'no-process-mirror']
    type: str
  pn_log_packets:
    description
      - Specify log packets in the vFlow or not.
    choices: ['log-packets', 'no-log-packets']
    type: str
  pn_log_stats:
    description
      - Specify log packet statistics for the flow or not.
    choices: ['log-stats', 'no-log-stats']
    type: str
  pn_packet_log_max:
    description
      - Specify maximum packet count for log rotation in the flow.
    type: str
  pn_stats_interval:
    description
      - Specify interval to update packet statistics for the log (in seconds).
    type: str
  pn_dur:
    description
      - Specify minimum duration required for the flow to be captured (in secs).
    type: str
  pn_metadata:
    description
      - Specify metadata number for the vflow.
    type: str
  pn_transient:
    description
      - Specify capture transient flows or not.
    choices: ['transient', 'no-transient']
    type: str
  pn_vxlan_ether_type:
    description:
      - Specify the VXLAN ether type for the vFlow.
    choices: ['ipv4', 'arp', 'wake', 'rarp', 'vlan' ,'ipv6', 'mpls-uni', 'mpls-
    multi', 'jumbo', 'aoe', 'dot1X', 'lldp', 'ecp', 'macsec', 'ptp, 'fcoe,
    'fcoe-init', ''qinq']
    type: str
  pn_vxlan:
    description
      - Specify the name of VXLAN for the vFlow.
    type: str
  pn_vxlan_proto:
    description
      - Specify protocol type for the VXLAN.
    choices: ['tcp', 'udp', 'icmp', 'igmp', 'ip']
    type: str
  pn_set_src:
    description
      - Specify src ip of ipv4 packets to set.
    type: str
  pn_set_dst:
    description
      - Specify dst ip of ipv4 packets to set.
    type: str
  pn_set_src_port:
    description
      - Specify src port of ipv4 packets to set.
    type: str
  pn_set_dst_port:
    description
      - Specify dst port of ipv4 packets to set.
    type: str
  pn_enable:
    description
      - Specify enable or disable flows in hardware or not.
    choices: ['enable', 'no-enable']
    type: str
"""

EXAMPLES = """
- name: create vflow
  pn_vflow:
    pn_command: 'vflow-create'
    pn_name: 'drop_src_packets'
    pn_scope: 'local'
    pn_src_ip: '10.10.100.1'
    pn_action: 'drop'

- name: delete vflow
  pn_vflow:
    pn_command: 'vflow-delete'
    pn_name: 'drop_src_packets'
"""

RETURN = """
command:
  description: the CLI command run on the target node(s).
stdout:
  description: the set of responses from the vFlow command.
  returned: always
  type: list
stderr:
  description: the set of error responses from the vFlow command.
  returned: on error
  type: list
changed:
  description: Indicates whether the CLI caused changes on the target.
  returned: always
  type: bool
"""


def pn_cli(module):
    """
    This method is to generate the cli portion to launch the Netvisor cli.
    It parses the username, password, switch parameters from module.
    :param module: The Ansible module to fetch username, password and switch
    :return: returns the cli string for further processing
    """
    username = module.params['pn_cliusername']
    password = module.params['pn_clipassword']

    if username and password:
        cli = '/usr/bin/cli --quiet --user %s:%s ' % (username, password)
    else:
        cli = '/usr/bin/cli --quiet '

    return cli


def check_vflow_exists(module, cli):
    """
    This method checks for idempotency using the vflow-show command.
    If a vFlow with given name exists, return True else False.
    :param module: The Ansible module to fetch input parameters
    :param cli: The CLI string
    :return True/False
    """
    name = module.params['pn_name']
    show = cli + ' vflow-show format switch,name no-show-headers'
    show = shlex.split(show)
    out = module.run_command(show)[1]
    out = out.split()

    return True if name in out else False


def run_cli(module, cli):
    """
    This method executes the cli command on the target node(s) and returns the
    output. The module then exits based on the output.
    :param cli: the complete cli string to be executed on the target node(s).
    :param module: The Ansible module to fetch command
    """
    command = module.params['pn_command']
    cmd = shlex.split(cli)
    rc, out, err = module.run_command(cmd)

    # Response in JSON format
    if err:
        module.exit_json(
            failed=True,
            stderr=err.strip(),
            msg="%s operation failed" % command,
            changed=False
        )

    if out:
        module.exit_json(
            stdout=out.strip(),
            msg="%s operation completed" % command,
            changed=True
        )

    else:
        module.exit_json(
            msg="%s operation completed" % command,
            changed=True
        )


def main():
    """ This portion is for arguments parsing """
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=False, type='str'),
            pn_clipassword=dict(required=False, type='str'),
            pn_cliswitch=dict(required=False, type='str', default='local'),
            pn_command=dict(required=True, type='str',
                            choices=['vflow-create', 'vflow-delete',
                                     'vflow-modify']),
            pn_name=dict(required=True, type='str'),
            pn_scope=dict(required=False, type='str',
                          choices=['local', 'fabric']),
            pn_vnet=dict(required=False, type='str'),
            pn_vlan=dict(required=False, type='str'),
            pn_in_port=dict(required=False, type='str'),
            pn_out_port=dict(required=False, type='str'),
            pn_ether_type=dict(required=False, type='str',
                               choices=['ipv4', 'arp', 'wake', 'rarp', 'vlan',
                                        'ipv6', 'mpls-uni', 'mpls-multi',
                                        'jumbo', 'aoe', 'dot1X', 'lldp', 'ecp',
                                        'macsec', 'ptp', 'fcoe', 'fcoe-init',
                                        'qinq']),
            pn_src_mac=dict(required=False, type='str'),
            pn_src_mac_mask=dict(required=False, type='str'),
            pn_dst_mac=dict(required=False, type='str'),
            pn_dst_mac_mask=dict(required=False, type='str'),
            pn_src_ip=dict(required=False, type='str'),
            pn_src_ip_mask=dict(required=False, type='str'),
            pn_dst_ip=dict(required=False, type='str'),
            pn_dst_ip_mask=dict(required=False, type='str'),
            pn_src_port=dict(required=False, type='str'),
            pn_src_port_mask=dict(required=False, type='str'),
            pn_dst_port=dict(required=False, type='str'),
            pn_dst_port_mask=dict(required=False, type='str'),
            pn_dscp_start=dict(required=False, type='str'),
            pn_dscp_end=dict(required=False, type='str'),
            pn_dscp=dict(required=False, type='str'),
            pn_tos_start=dict(required=False, type='str'),
            pn_tos_end=dict(required=False, type='str'),
            pn_tos=dict(required=False, type='str'),
            pn_vlan_pri=dict(required=False, type='str'),
            pn_ttl=dict(required=False, type='str'),
            pn_proto=dict(required=False, type='str',
                          choices=['tcp', 'udp', 'icmp', 'igmp', 'ip']),
            pn_flow_class=dict(required=False, type='str'),
            pn_ingress_tunnel=dict(required=False, type='str'),
            pn_egress_tunnel=dict(required=False, type='str'),
            pn_bw_min=dict(required=False, type='str'),
            pn_bw_max=dict(required=False, type='str'),
            pn_precendence=dict(required=False, type='str'),
            pn_action=dict(required=False, type='str',
                           choices=['none', 'drop', 'to-port', 'to-cpu', 'trap',
                                    'copy-to-cpu', 'copy-to-port', 'check',
                                    'setvlan', 'tunnel-pkt', 'set-tunnel-id',
                                    'to-span', 'cpu-rx', 'cpu-rx-tx',
                                    'set-metadata', 'set-dscp', 'decap',
                                    'set-dmac', 'set-dmac-to-port',
                                    'to-ports-and-cpu', 'set-vlan-pri',
                                    'tcp-seq-offset', 'tcp-ack-offset',
                                    'l3-to-cpu-switch']),
            pn_action_value=dict(required=False, type='str'),
            pn_action_set_mac_value=dict(required=False, type='str'),
            pn_action_to_ports_value=dict(required=False, type='str'),
            pn_mirror=dict(required=False, type='str'),
            pn_process_mirror=dict(required=False, type='str',
                                   choices=['process-mirror',
                                            'no-process-mirror']),
            pn_log_packets=dict(required=False, type='str',
                                choices=['log-packets', 'no-log-packets']),
            pn_log_stats=dict(required=False, type='str',
                              choices=['log-stats', 'no-log-stats']),
            pn_packet_log_max=dict(required=False, type='str'),
            pn_stats_interval=dict(required=False, type='str'),
            pn_dur=dict(required=False, type='str'),
            pn_metadata=dict(required=False, type='str'),
            pn_transient=dict(required=False, type='str',
                              choices=['transient', 'no-transient']),
            pn_vxlan_ether_type=dict(required=False, type='str',
                                     choices=['ipv4', 'arp', 'wake', 'rarp',
                                              'vlan', 'ipv6', 'mpls-uni',
                                              'mpls-multi', 'jumbo', 'aoe',
                                              'dot1X', 'lldp', 'ecp', 'macsec',
                                              'ptp', 'fcoe', 'fcoe-init',
                                              'qinq']),
            pn_vxlan=dict(required=False, type='str'),
            pn_vxlan_proto=dict(required=False, type='str',
                                choices=['tcp', 'udp', 'icmp', 'igmp', 'ip']),
            pn_set_src=dict(required=False, type='str'),
            pn_set_dst=dict(required=False, type='str'),
            pn_set_src_port=dict(required=False, type='str'),
            pn_set_dst_port=dict(required=False, type='str'),
            pn_enable=dict(required=False, type='str',
                           choices=['enable', 'no-enable']),
        ),
        required_if=(
            ["pn_command", "vflow-create", ["pn_name", "pn_scope"]],
            ["pn_command", "vflow-delete", ["pn_name"]],
            ["pn_command", "vflow-modify", ["pn_name"]]
        )
    )

    # Accessing the arguments
    command = module.params['pn_command']
    name = module.params['pn_name']
    scope = module.params['pn_scope']
    vnet = module.params['pn_vnet']
    vlan = module.params['pn_vlan']
    in_port = module.params['pn_in_port']
    out_port = module.params['pn_out_port']
    ether_type = module.params['pn_ether_type']
    src_mac = module.params['pn_src_mac']
    src_mac_mask = module.params['pn_src_mac_mask']
    dst_mac = module.params['pn_dst_mac']
    dst_mac_mask = module.params['pn_dst_mac_mask']
    src_ip = module.params['pn_src_ip']
    src_ip_mask = module.params['pn_src_ip_mask']
    dst_ip = module.params['pn_dst_ip']
    dst_ip_mask = module.params['pn_dst_ip_mask']
    src_port = module.params['pn_src_port']
    src_port_mask = module.params['pn_src_port_mask']
    dst_port = module.params['pn_dst_port']
    dst_port_mask = module.params['pn_dst_port_mask']
    dscp_start = module.params['pn_dscp_start']
    dscp_end = module.params['pn_dscp_end']
    dscp = module.params['pn_dscp']
    tos_start = module.params['pn_tos_start']
    tos_end = module.params['pn_tos_end']
    tos = module.params['pn_tos']
    vlan_pri = module.params['pn_vlan_pri']
    ttl = module.params['pn_ttl']
    proto = module.params['pn_proto']
    flow_class = module.params['pn_flow_class']
    ingress_tunnel = module.params['pn_ingress_tunnel']
    egress_tunnel = module.params['pn_egress_tunnel']
    bw_min = module.params['pn_bw_min']
    bw_max = module.params['pn_bw_max']
    precedence = module.params['pn_precendence']
    action = module.params['pn_action']
    action_value = module.params['pn_action_value']
    action_set_mac_value = module.params['pn_action_set_mac_value']
    action_to_ports_value = module.params['pn_action_to_ports_value']
    mirror = module.params['pn_mirror']
    process_mirror = module.params['pn_process_mirror']
    log_packets = module.params['pn_log_packets']
    log_stats = module.params['pn_log_stats']
    packet_log_max = module.params['pn_packet_log_max']
    stats_interval = module.params['pn_stats_interval']
    duration = module.params['pn_dur']
    metadata = module.params['pn_metadata']
    transient = module.params['pn_transient']
    vxlan_ether_type = module.params['pn_vxlan_ether_type']
    vxlan = module.params['pn_vxlan']
    vxlan_proto = module.params['pn_vxlan_proto']
    set_src = module.params['pn_set_src']
    set_dst = module.params['pn_set_dst']
    set_src_port = module.params['pn_set_src_port']
    set_dst_port = module.params['pn_set_dst_port']
    enable = module.params['pn_enable']

    # Building the CLI command string
    cli = pn_cli(module)

    if command == 'vflow-delete':
        if not check_vflow_exists(module, cli):
            module.exit_json(
                skipped=True,
                msg='vFlow with name %s does not exist' % name
            )

        cli += ' %s name %s ' % (command, name)
    else:
        if command == 'vflow-create':
            if check_vflow_exists(module, cli):
                module.exit_json(
                    skipped=True,
                    msg='vFlow with name %s already exists' % name
                )

        cli += ' %s name %s ' % (command, name)

        # Appending options
        if scope:
            cli += ' scope ' + scope

        if vnet:
            cli += ' vnet ' + vnet

        if vlan:
            cli += ' vlan ' + vlan

        if in_port:
            cli += ' in-port ' + in_port

        if out_port:
            cli += ' out-port ' + out_port

        if ether_type:
            cli += ' ether-type ' + ether_type

        if src_mac:
            cli += ' src-mac ' + src_mac

        if src_mac_mask:
            cli += ' src-mac-mask ' + src_mac_mask

        if dst_mac:
            cli += ' dst-mac ' + dst_mac

        if dst_mac_mask:
            cli += ' dst-mac-mask ' + dst_mac_mask

        if src_ip:
            cli += ' src-ip ' + src_ip

        if src_ip_mask:
            cli += ' src-ip-mask ' + src_ip_mask

        if dst_ip:
            cli += ' dst-ip ' + dst_ip

        if dst_ip_mask:
            cli += ' dst-ip-mask ' + dst_ip_mask

        if src_port:
            cli += ' src-port ' + src_port

        if src_port_mask:
            cli += ' src-port-mask ' + src_port_mask

        if dst_port:
            cli += ' dst-port ' + dst_port

        if dst_port_mask:
            cli += ' dst-port-mask ' + dst_port_mask

        if dscp_start:
            cli += ' dscp-start ' + dscp_start

        if dscp_end:
            cli += ' dscp-end ' + dscp_end

        if dscp:
            cli += ' dscp ' + dscp

        if tos_start:
            cli += ' tos-start ' + tos_start

        if tos_end:
            cli += ' tos-end ' + tos_end

        if tos:
            cli += ' tos ' + tos

        if vlan_pri:
            cli += ' vlan-pri ' + vlan_pri

        if ttl:
            cli += ' ttl ' + ttl

        if proto:
            cli += ' proto ' + proto

        if flow_class:
            cli += ' flow-class ' + flow_class

        if ingress_tunnel:
            cli += ' ingress-tunnel ' + ingress_tunnel

        if egress_tunnel:
            cli += ' egress-tunnel ' + egress_tunnel

        if bw_min:
            cli += ' bw-min ' + bw_min

        if bw_max:
            cli += ' bw-max ' + bw_max

        if precedence:
            cli += ' precedence ' + precedence

        if action:
            cli += ' action ' + action

        if action_value:
            cli += ' action-value ' + action_value

        if action_set_mac_value:
            cli += ' action-set-mac-value ' + action_set_mac_value

        if action_to_ports_value:
            cli += ' action-to-ports-value ' + action_to_ports_value

        if mirror:
            cli += ' mirror ' + mirror

        if process_mirror:
            cli += ' ' + process_mirror

        if log_packets:
            cli += ' ' + log_packets

        if packet_log_max:
            cli += ' packet-log-max ' + packet_log_max

        if log_stats:
            cli += ' ' + log_stats

        if stats_interval:
            cli += ' stats-interval ' + stats_interval

        if duration:
            cli += ' dur ' + duration

        if metadata:
            cli += ' metadata ' + metadata

        if transient:
            cli += ' ' + transient

        if vxlan:
            cli += ' vxlan ' + vxlan

        if vxlan_ether_type:
            cli += ' vxlan-ether-type ' + vxlan_ether_type

        if vxlan_proto:
            cli += ' vxlan-proto ' + vxlan_proto

        if set_src:
            cli += ' set-src ' + set_src

        if set_dst:
            cli += ' set-dst ' + set_dst

        if set_src_port:
            cli += ' set-src-port ' + set_src_port

        if set_dst_port:
            cli += ' set-dst-port ' + set_dst_port

        if enable:
            cli += ' ' + enable

    run_cli(module, cli)

# Ansible boiler-plate
from ansible.module_utils.basic import AnsibleModule

if __name__ == '__main__':
    main()

