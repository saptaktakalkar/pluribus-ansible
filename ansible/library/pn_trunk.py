#!/usr/bin/python
# Test PN CLI trunk-create/trunk-delete/trunk-modify

import subprocess
import shlex
from ansible.module_utils.basic import *

DOCUMENTATION = """
---
module: pn_trunk
author: "Pluribus Networks"
short_description: CLI command to create/delete a trunk
description:
  - Execute trunk-create or trunk-delete command. 
  - Requires trunk name:
    - Alphanumeric characters
    - Special characters like: _
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
  pn_trunkcommand:
    description:
      - The C(pn_trunkcommand) takes the trunk commands as value.
    required: true
    choices: trunk-create, trunk-delete, trunk-modify
    type: str
  pn_trunkname:
    description:
      - The C(pn_trunkname) takes a valid name for trunk configuration.
    required: true
    type: str
  pn_trunkports:
    description:
      - comma separated list of ports for the trunk 
    required_if: trunk-create 
    type: str
  pn_trunkspeed:
    description:
      - physical port speed
    required: false
    choices: disable, 10m, 100m, 1g, 2.5g, 10g, 40g
    type: str
  pn_trunkegress:
    description:
      - max egress port data rate limit
    required: false
    type: str
  pn_trunkjumbo:
    description
      - jumbo frames on physical port (jumbo|no-jumbo)
    required: false
    type: bool  
  pn_trunklacpmode:
    description:
      - LACP mode of physical mode
    required: false
    choices: off, passive, active
    type: str
  pn_trunklacppriority:
    description
      - LACP priority from 1 to 65535(defaut: 32768)
    required: false
    type: str
  pn_trunklacptimeout:
    description:
      - LACP timeout(default: slow)
    required: false
    choices: slow, fast
    type: str
  pn_trunkfallback:
    description:
      - LACP fallback mode
    required: false
    choices: bundle, individual
  pn_trunkfallbacktimeout:
    description: 
      - LACP fallback timeout 30..60 seconds(default: 50)
    required: false
    type: str
  pn_trunkedge:
    description:
      - physical port edge switch(edge-switch|no-edge-switch)
    required: false
    type: bool
  pn_trunkpause:
    description: 
      - physical port pause(pause|no-pause)
    required: false
    type: bool
  pn_trunkdesc:
    description:
      - physical port description
    required: true
    type: str
  pn_trunkloopback:
    description;
      - physical port loopback(loopback|no-loopback)
    required: false
    type: bool
  pn_trunkucastlevel:
    description:
      - unknown unicast level in % (default 30%)
    required: false
    type: str
  pn_trunkmcastlevel:
    description:
      - unknown multicast level in % (default 30%)
    required: false
    type: str
  pn_trunkbcastlevel:
    description: 
      - broadcast level in % (default 30%)
    required: false
    type: str
  pn_trunkportmacaddr:
    description:
      - physical port MAC address
    required: false
    type: str
  pn_trunkloopvlans:
    description: 
      - list of looping vlans
    required: false
    type: str
  pn_trunkrouting:
    description: 
      - routing(routing|no-routing)
    required: false
    type: bool
  pn_trunkhost:
    description: 
      - host facing port control setting(host-enable|host-disable)
    required: false
    type: bool
  pn_quiet:
    description:
      - The C(pn_quiet) option to enable or disable the system bootup message
    required: false
    type: bool
    default: true
"""

EXAMPLES = """
- name: create trunk 
  pn_trunk:
    pn_cliusername: admin
    pn_clipassword: admin
    pn_trunkcommand: 'trunk-create'
    pn_trunkname: 'trunk-1'
    pn_trunkports: '10...14'
    pn_trunkspeed: '40g'
    pn_trunkedge: True
    pn_quiet: True
- name: modify trunk 
  pn_trunk:
    pn_cliusername: admin
    pn_clipassword: admin
    pn_trunkcommand: 'trunk-modify'
    pn_trunkname: 'trunk-1' pn_trunkspeed: '10g'
    pn_trunklacpmode: 'passive'
    pn_trunkedge: True
    pn_quiet: True
- name: delete trunk 
  pn_trunk:
    pn_cliusername: admin
    pn_clipassword: admin
    pn_trunkcommand: 'trunk-delete'
    pn_trunkname: 'trunk-1'
    pn_quiet: True
"""

RETURN = """
trunkcmd:
  description: the CLI command run on the target node(s).
stdout:
  description: the set of responses from the trunk command.
  returned: always
  type: list
stdout_lines:
  description: the value of stdout split into a list.
  returned: always
  type: list
stderr:
  description: the set of error responses from the trunk command.
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
            pn_trunkcommand=dict(required=True, type='str',
                                 choices=['trunk-create', 'trunk-delete',
                                          'trunk-modify']),
            pn_trunkname=dict(required=True, type='str'),
            pn_trunkports=dict(type='str'),
            pn_trunkspeed=dict(required=False, type='str',
                               choices=['disable', '10m', '100m', '1g', '2.5g',
                                        '10g', '40g']),
            pn_trunkegress=dict(required=False, type='str'),
            pn_trunkjumbo=dict(required=False, type='bool'),
            pn_trunklacpmode=dict(required=False, type='str',
                                  choices=['off', 'passive', 'active']),
            pn_trunklacppriority=dict(required=False, type='str'),
            pn_trunklacptimeout=dict(required=False, type='str',
                                     choices=['slow', 'fast']),
            pn_trunkfallback=dict(required=False, type='str',
                                  choices=['bundle', 'individual']),
            pn_trunkfallbacktimeout=dict(required=False, type='str'),
            pn_trunkedge=dict(required=False, type='bool'),
            pn_trunkpause=dict(required=False, type='bool'),
            pn_trunkdesc=dict(required=False, type='str'),
            pn_trunkloopback=dict(required=False, type='bool'),
            pn_trunkucastlevel=dict(required=False, type='str'),
            pn_trunkmcastlevel=dict(required=False, type='str'),
            pn_trunkbcastlevel=dict(required=False, type='str'),
            pn_trunkportmacaddr=dict(required=False, type='str'),
            pn_trunkloopvlans=dict(required=False, type='str'),
            pn_trunkrouting=dict(required=False, type='bool'),
            pn_trunkhost=dict(required=False, type='bool'),
            pn_quiet=dict(default=True, type='bool')
        ),
        required_if=(
            ["pn_trunkcommand", "trunk-create",
             ["pn_trunkname", "pn_trunkports"]],
            ["pn_trunkcommand", "trunk-delete", ["pn_trunkname"]],
            ["pn_trunkcommand", "trunk-modify", ["pn_trunkname"]]
        )
    )

    cliusername = module.params['pn_cliusername']
    clipassword = module.params['pn_clipassword']
    trunkcommand = module.params['pn_trunkcommand']
    trunkname = module.params['pn_trunkname']
    trunkports = module.params['pn_trunkports']
    trunkspeed = module.params['pn_trunkspeed']
    trunkegress = module.params['pn_trunkegress']
    trunkjumbo = module.params['pn_trunkjumbo']
    trunklacpmode = module.params['pn_trunklacpmode']
    trunklacppriority = module.params['pn_trunklacppriority']
    trunklacptimeout = module.params['pn_trunklacptimeout']
    trunkfallback = module.params['pn_trunkfallback']
    trunkfallbacktimeout = module.params['pn_trunkfallbacktimeout']
    trunkedge = module.params['pn_trunkedge']
    trunkpause = module.params['pn_trunkpause']
    trunkdesc = module.params['pn_trunkdesc']
    trunkloopback = module.params['pn_trunkloopback']
    trunkucastlevel = module.params['pn_trunkucastlevel']
    trunkmcastlevel = module.params['pn_trunkmcastlevel']
    trunkbcastlevel = module.params['pn_trunkbcastlevel']
    trunkportmacaddr = module.params['pn_trunkportmacaddr']
    trunkloopvlans = module.params['pn_trunkloopvlans']
    trunkrouting = module.params['pn_trunkrouting']
    trunkhost = module.params['pn_trunkhost']
    quiet = module.params['pn_quiet']

    if quiet is True:
        cli = ('/usr/bin/cli --quiet --user ' + cliusername + ':' +
               clipassword + ' ')
    else:
        cli = '/usr/bin/cli --user ' + cliusername + ':' + clipassword + ' '

    trunk = cli
    if trunkname:
        trunk += trunkcommand + ' name ' + trunkname

    if trunkports:
        trunk += ' ports ' + trunkports

    if trunkspeed:
        trunk += ' speed ' + trunkspeed

    if trunkegress:
        trunk += ' egress-rate-limit ' + trunkegress

    if trunkjumbo is True:
        trunk += ' jumbo '
    if trunkjumbo is False:
        trunk += ' no-jumbo '

    if trunklacpmode:
        trunk += ' lacp-mode ' + trunklacpmode

    if trunklacppriority:
        trunk += ' lacp-priority ' + trunklacppriority

    if trunklacptimeout:
        trunk += ' lacp-timeout ' + trunklacptimeout

    if trunkfallback:
        trunk += ' lacp-fallback ' + trunkfallback

    if trunkfallbacktimeout:
        trunkfallbacktimeout += ' lacp-fallback-timeout ' + trunkfallbacktimeout

    if trunkedge is True:
        trunk += ' edge-switch '
    if trunkedge is False:
        trunk += ' no-edge-switch '

    if trunkpause is True:
        trunk += ' pause '
    if trunkpause is False:
        trunk += ' no-pause '

    if trunkdesc:
        trunk += ' description ' + trunkdesc

    if trunkloopback is True:
        trunk += ' loopback '
    if trunkloopback is False:
        trunk += ' no-loopback '

    if trunkucastlevel:
        trunk += ' unknown-ucast-level ' + trunkucastlevel

    if trunkmcastlevel:
        trunk += ' unknown-mcast-level ' + trunkmcastlevel

    if trunkbcastlevel:
        trunk += ' broadcast-level ' + trunkbcastlevel

    if trunkportmacaddr:
        trunk += ' port-mac-address ' + trunkportmacaddr

    if trunkloopvlans:
        trunk += ' loopvlans ' + trunkloopvlans

    if trunkrouting is True:
        trunk += ' routing '
    if trunkrouting is False:
        trunk += ' no-routing '

    if trunkhost is True:
        trunk += ' host-enable '
    if trunkhost is False:
        trunk += ' host-disable '

    trunkcmd = shlex.split(trunk)
    response = subprocess.Popen(trunkcmd, stderr=subprocess.PIPE,
                                stdout=subprocess.PIPE, universal_newlines=True)
    out, err = response.communicate()

    if out:
        module.exit_json(
            trunkcmd=trunk,
            stdout=out.rstrip("\r\n"),
            changed=True
        )
    if err:
        module.exit_json(
            trunkcmd=trunk,
            stderr=err.rstrip("\r\n"),
            changed=False
        )

if __name__ == '__main__':
    main()
