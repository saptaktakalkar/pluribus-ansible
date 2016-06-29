#!/usr/bin/python
# Test PN-CLI vrouter-interface commands

import subprocess
import shlex
from ansible.module_utils.basic import *

DOCUMENTATION = """
---
module: pn_vrouterif
author: "Pluribus Networks"
short_description: CLI command to add/remove/modify vrouter-interface
description:
  - Execute vrouter-interface-add, vrouter-interface-remove,
    vrouter-interface-modify command.
  - Add/remove/modify interface for a vrouter
options:
  pn_cliusername:
    description:
      - Login username
    required: true
    type: str
  pn_clipassword:
    description:
      - Login password
    required: true
    type: str
  pn_vrouterifcommand:
    description:
      - The C(pn_vrouterifcommand) takes the vrouter-interface command as value.
    required: true
    choices: vrouter-interface-add, vrouter-interface-remove,
             vrouter-interface-modify
    type: str
  pn_vrouterifname:
    description:
      - name for service config
    required: true
    type: str
  pn_vrouterifvlan:
    description:
      - interface VLAN
    required_if: vrouter-interface-add 
    type: int
  pn_vrouterifip:
    description:
      - IP address
    required: false
    type: str
  pn_vrouterifnetmask:
    description:
      - netmask
    required: false
    type: str
  pn_vrouterifassign: 
    description: 
      - type of IP address assignment
    required: false
    type: str
  pn_vrouterifvxlan:
    description: 
      - interface vxlan
    required: false
    type: str
  pn_vrouterif_interface:
    description:
      - interface type
    required: false
    type: str
  pn_vrouterifalias:
    description: 
      - alias name
    required: false
    type: str
  pn_vrouterifexclusive:
    description: 
      - exclusive interface
    required: false
    type: bool
  pn_vrouterifnic:
    description:
      - NIC config
    required: false
    type: bool
  pn_vrouterifvrrpid:
    description:
      - ID assigned to VRRP
    required: false
    type: int
  pn_vrouterifvrrp_primary:
    description:
      - VRRP Primary interface
    required: false
    type: str
  pn_vrouterifvrrp_priority:
    description:
      - VRRP priority for interface
    required: false
    type: int
  pn_vrouterifvrrp_advint:
    description:
      - VRRP advertisement intervals(ms,min 10, max 40950, default 1000)
    required: false
    type: str
  pn_vrouterifl3port:
    description:
      - Layer 3 port
    required: false
    type: str
  pn_vrouterifsecmacs:
    description:
      - secondary MAC addresses
    required: false
    type: str
  pn_vrouterifnicstr:
    description:
      - virtual NIC assigned to the interface
    required: false
    type: str
  pn_quiet:
    description:
      - The C(pn_quiet) option to enable or disable the system bootup message
    required: false
    type: bool
    default: true
"""

EXAMPLES = """
- name: add vrouter-interface 
  pn_vrouterif:
    pn_cliusername: admin
    pn_clipassword: admin
    pn_vrouterifcommand: 'vrouter-interface-add'
    pn_vrouterifname: 'ansible-vrouter'
    pn_vrouterifvlan: 104
    pn_quiet: True

- name: remove vrouter-interface 
  pn_vrouterif: 
    pn_cliusername: admin
    pn_clipassword: admin
    pn_vrouterifcommand: 'vrouter-interface-remove'
    pn_vrouterifname: 'ansible-vrouter'
    pn_vrouterifnicstr: 'eth-104'
    pn_quiet: True
"""

RETURN = """
vrouterifcmd:
  description: the CLI command run on the target node(s).
stdout:
  description: the set of responses from the vrouterif command.
  returned: always
  type: list
stdout_lines:
  description: the value of stdout split into a list.
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
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=True, type='str'),
            pn_clipassword=dict(required=True, type='str'),
            pn_vrouterifcommand=dict(required=True, type='str',
                                     choices=['vrouter-interface-add',
                                              'vrouter-interface-remove',
                                              'vrouter-interface-modify']),
            pn_vrouterifname=dict(required=True, type='str'),
            pn_vrouterifvlan=dict(required=False, type='int'),
            pn_vrouterifip=dict(required=False, type='str'),
            pn_vrouterifnetmask=dict(required=False, type='str'),
            pn_vrouterifassign=dict(required=False, type='str',
                                    choices=['none', 'dhcp', 'dhcpv6',
                                             'autov6']),
            pn_vrouterifvxlan=dict(required=False, type='str'),
            pn_vrouterif_interface=dict(required=False, type='str',
                                        choices=['mgmt', 'data', 'span']),
            pn_vrouterifalias=dict(required=False, type='str'),
            pn_vrouterifexclusive=dict(required=False, type='bool'),
            pn_vrouterifnic=dict(required=False, type='bool'),
            pn_vrouterifvrrpid=dict(required=False, type='int'),
            pn_vrouterifvrrp_primary=dict(required=False, type='str'),
            pn_vrouterifvrrp_priority=dict(required=False, type='int'),
            pn_vrouterifvrrp_advint=dict(required=False, type='str'),
            pn_vrouterifl3port=dict(required=False, type='str'),
            pn_vrouterifsecmacs=dict(required=False, type='str'),
            pn_vrouterifnicstr=dict(required=False, type='str'),
            pn_quiet=dict(default=True, type='bool')
        ),
        required_if=(
            ["pn_vrouterifcommand", "vrouter-interface-add",
             ["pn_vrouterifname", "pn_vrouterifvlan"]],
            ["pn_vrouterifcommand", "vrouter-interface-remove",
             ["pn_vrouterifname", "pn_vrouterifnicstr"]],
            ["pn_vrouterifcommand", "vrouter-interface-modify",
             ["pn_vrouterifname", "pn_vrouterifnicstr"]]
        ),
    )

    cliusername = module.params['pn_cliusername']
    clipassword = module.params['pn_clipassword']
    vrouterifcommand = module.params['pn_vrouterifcommand']
    vrouterifname = module.params['pn_vrouterifname']
    vrouterifvlan = module.params['pn_vrouterifvlan']
    vrouterifip = module.params['pn_vrouterifip']
    vrouterifnetmask = module.params['pn_vrouterifnetmask']
    vrouterifassign = module.params['pn_vrouterifassign']
    vrouterifvxlan = module.params['pn_vrouterifvxlan']
    vrouterif_interface = module.params['pn_vrouterif_interface']
    vrouterifalias = module.params['pn_vrouterifalias']
    vrouterifexclusive = module.params['pn_vrouterifexclusive']
    vrouterifnic = module.params['pn_vrouterifnic']
    vrouterifvrrpid = module.params['pn_vrouterifvrrpid']
    vrouterifvrrp_primary = module.params['pn_vrouterifvrrp_primary']
    vrouterifvrrp_priority = module.params['pn_vrouterifvrrp_priority']
    vrouterifvrrp_advint = module.params['pn_vrouterifvrrp_advint']
    vrouterifl3port = module.params['pn_vrouterifl3port']
    vrouterifsecmacs = module.params['pn_vrouterifsecmacs']
    vrouterifnicstr = module.params['pn_vrouterifnicstr']
    quiet = module.params['pn_quiet']

    if quiet is True:
        cli = ('/usr/bin/cli --quiet --user ' + cliusername + ':' +
               clipassword + ' ')
    else:
        cli = '/usr/bin/cli --user ' + cliusername + ':' + clipassword + ' '

    vrouterif = cli
    if vrouterifname:
        vrouterif = cli + vrouterifcommand + ' vrouter-name ' + vrouterifname

    if vrouterifvlan:
        vrouterif += ' vlan ' + str(vrouterifvlan)

    if vrouterifip:
        vrouterif += ' ip ' + vrouterifip

    if vrouterifnetmask:
        vrouterif += ' netmask ' + vrouterifnetmask

    if vrouterifassign:
        vrouterif += ' assignment ' + vrouterifassign

    if vrouterifvxlan:
        vrouterif += ' vxlan ' + vrouterifvxlan

    if vrouterif_interface:
        vrouterif += ' if ' + vrouterif_interface

    if vrouterifalias:
        vrouterif += ' alias-on ' + vrouterifalias

    if vrouterifexclusive is True:
        vrouterif += ' exclusive '
    if vrouterifexclusive is False:
        vrouterif += ' no-exclusive '

    if vrouterifnic is True:
        vrouterif += ' nic-enable '
    if vrouterifnic is False:
        vrouterif += ' nic-disable '

    if vrouterifvrrpid:
        vrouterif += ' vrrp-id ' + str(vrouterifvrrpid)

    if vrouterifvrrp_primary:
        vrouterif += ' vrrp-primary ' + vrouterifvrrp_primary

    if vrouterifvrrp_priority:
        vrouterif += ' vrrp-priority ' + str(vrouterifvrrp_priority)

    if vrouterifvrrp_advint:
        vrouterif += ' vrrp-adv-int ' + vrouterifvrrp_advint

    if vrouterifl3port:
        vrouterif += ' l3-port ' + vrouterifl3port

    if vrouterifsecmacs:
        vrouterif += ' secondary-macs ' + vrouterifsecmacs

    if vrouterifnicstr:
        vrouterif += ' nic ' + vrouterifnicstr

    vrouterifcmd = shlex.split(vrouterif)
    response = subprocess.Popen(vrouterifcmd, stderr=subprocess.PIPE,
                                stdout=subprocess.PIPE, universal_newlines=True)
    out, err = response.communicate()

    if out:
        module.exit_json(
            vrouterifcmd=vrouterif,
            stdout=out.rstrip("\r\n"),
            changed=True
        )

    if err:
        module.exit_json(
            vrouterifcmd=vrouterif,
            stderr=err.rstrip("\r\n"),
            changed=False
        )

if __name__ == '__main__':
    main()
