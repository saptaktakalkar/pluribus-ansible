#!/usr/bin/python
# Test PN-CLI vrouter-bgp commands

DOCUMENTATION = """
---
module: pn_vrouterbgp
author: "Pluribus Networks"
short_description: CLI command to add/remove/modify vrouter-bgp
description:
  - Execute vrouter-bgp-add, vrouter-bgp-remove, vrouter-bgp-modify command. 
  - Add/remove/modify Border Gateway Protocol neighbor to a vrouter
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
  pn_vrouterbgp_command:
    description:
      - The C(pn_vrouterbgp_command) takes the vrouter-bgp-add/vrouter-bgp-remove/vrouter-bgp-modify command as value.
    required: true
    choices: vrouter-bgp-add, vrouter-bgp-remove, vrouter-bgp-modify
    type: str
  pn_vrouterbgp_name:
    description:
      - name for service config
    required: true
    type: str
  pn_vrouterbgp_neighbor:
    description:
      - IP address for the BGP neighbor
    required_if: vrouter-bgp-add 
    type: str
  pn_vrouterbgp_remote_as:
    description:
      - BGP remote AS from 1 to 4294967295
    required_if: vrouter-bgp-add
    type: int
  pn_vrouterbgp_nexthop:
    description:
      - BGP next hop is self or not
    required: false
    type: bool
  pn_vrouterbgp_password: 
    description: 
      - password for MD5 BGP
    required: false
    type: str
  pn_vrouterbgp_ebgp:
    description: 
      - value for external BGP from 1 to 255
    required: false
    type: int
  pn_vrouterbgp_prefixlistin:
    description:
      - prefixes used for filtering  
    required: false
    type: str
  pn_vrouterbgp_prefixlistout:
    description: 
      - prefixes used for filtering outgoing packets
    required: false
    type: str
  pn_vrouterbgp_reflector:
    description: 
      - set as route reflector client
    required: false
    type: bool
  pn_vrouterbgp_capability:
    description:
      - override capability
    required: false
    type: bool
  pn_vrouterbgp_softreconfig:
    description:
      - soft reset to reconfigure inbound traffic
    required: false
    type: bool
  pn_vrouterbgp_maxprefix:
    description:
      - maximum number of prefixes
    required: false
    type: int
  pn_vrouterbgp_maxprefixwarn:
    description:
      - warn if maximum number of preifixes is exceeded
    required: false
    type: bool
  pn_vrouterbgp_bfd:
    description:
      - BFD protocol support for fault detection
    required: false
    type: bool
  pn_vrouterbgp_multiprotocol:
    description:
      - multi-protocol features
    required: false
    type: bool
  pn_vrouterbgp_weight:
    description:
      - default weight value between 0 and 65535 for the neighbor's routes
    required: false
    type: int
  pn_vrouterbgp_default:
    description:
      - announce default routes to the neighbor or not
    required: false
    type: bool
  pn_vrouterbgp_keepalive:
    description:
      - BGP keepalive interval in seconds
    required: false
    type: int
  pn_vrouterbgp_holdtime:
    description:
      - BGP holdtime in seconds
    required: false
    type: int
  pn_vrouterbgp_routemapin:
    description:
      - route map in for nbr
    required: false
    type: str
  pn_vrouterbgp_routemapout:
    description:
      - route map out for nbr
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
- name: add vrouter-bgp 
  pn_vrouterbgp: pn_cliusername=admin pn_clipassword=admin pn_vrouterbgp_command='vrouter-bgp-add' pn_vrouterbgp_name='ansible-vrouter' pn_vrouterbgp_neighbor=104.104.104.1 pn_vrouterbgp_remote_as=1800 pn_quiet=True

- name: remove vrouter-bgp 
  pn_vrouterbgp: pn_cliusername=admin pn_clipassword=admin pn_vrouterbgp_command='vrouter-delete' pn_vrouterbgp_name='ansible-vrouter' pn_vrouterbgp_neighbor=104.104.104.1 pn_quiet=True
"""

RETURN = """
vrouterbgpcmd:
  description: the CLI command run on the target node(s).
stdout:
  description: the set of responses from the vrouterbpg command.
  returned: always
  type: list
stdout_lines:
  description: the value of stdout split into a list.
  returned: always
  type: list
stderr:
  description: the set of error responses from the vrouterbgp command.
  returned: on error
  type: list
changed:
  description: Indicates whether the CLI caused changes on the target.
  returned: always
  type: bool
"""

import subprocess
import shlex
import json

def main():
        module = AnsibleModule(
                argument_spec = dict(
			pn_cliusername = dict(required=True, type='str'),
			pn_clipassword = dict(required=True, type='str'),
                        pn_vrouterbgp_command = dict(required=True, type='str', choices=['vrouter-bgp-add', 'vrouter-bgp-remove', 'vrouter-bgp-modify']),
                        pn_vrouterbgp_name = dict(required=True, type='str'),
                        pn_vrouterbgp_neighbor = dict(required=False, type='str'),
                        pn_vrouterbgp_remote_as = dict(required=False, type='int'), 
			pn_vrouterbgp_nexthop = dict(required=False, type='bool'),
			pn_vrouterbgp_password = dict(required=False, type='str'),
			pn_vrouterbgp_ebgp = dict(required=False, type='int'),
			pn_vrouterbgp_prefixlistin = dict(required=False, type='str'),
			pn_vrouterbgp_prefixlistout = dict(required=False, type='str'),
			pn_vrouterbgp_reflector = dict(required=False, type='bool'),
			pn_vrouterbgp_capability = dict(required=False, type='bool'),
			pn_vrouterbgp_softreconfig = dict(required=False, type='bool'),
			pn_vrouterbgp_maxprefix = dict(required=False, type='int'),
			pn_vrouterbgp_maxprefixwarn = dict(required=False, type='bool'),
			pn_vrouterbgp_bfd = dict(required=False, type='bool'),
			pn_vrouterbgp_multiprotocol = dict(required=False, type='bool', choices=['ipv4-unicast', 'ipv6-unicast']),
			pn_vrouterbgp_weight = dict(required=False, type='int'),
			pn_vrouterbgp_default = dict(required=False, type='bool'),
			pn_vrouterbgp_keepalive = dict(required=False, type='int'),
			pn_vrouterbgp_holdtime = dict(required=False, type='int'),
			pn_vrouterbgp_routemapin = dict(required=False, type='str'),
			pn_vrouterbgp_routemapout = dict(required=False, type='str'),
			pn_quiet = dict(default=True, type='bool')
                        ),
                required_if = (
                        [ "pn_vrouterbgp_command", "vrouter-bgp-add", [ "pn_vrouterbgp_name", "pn_vrouterbgp_neighbor", "pn_vrouterbgp_remote_as" ] ],
                        [ "pn_vrouterbgp_command", "vrouter-bgp-remove", [ "pn_vrouterbgp_name", "pn_vrouterbgp_neighbor" ] ],
			[ "pn_vrouterbgp_command", "vrouter-bgp-modify", [ "pn_vrouterbgp_name", "pn_vrouterbgp_neighbor" ] ]
                        )
        )

	cliusername = module.params['pn_cliusername']
	clipassword = module.params['pn_clipassword']
	vrouterbgp_command = module.params['pn_vrouterbgp_command']
	vrouterbgp_name = module.params['pn_vrouterbgp_name']
	vrouterbgp_neighbor = module.params['pn_vrouterbgp_neighbor']
	vrouterbgp_remote_as = module.params['pn_vrouterbgp_remote_as']
	vrouterbgp_nexthop = module.params['pn_vrouterbgp_nexthop']
	vrouterbgp_password = module.params['pn_vrouterbgp_password']
	vrouterbgp_ebgp = module.params['pn_vrouterbgp_ebgp']
	vrouterbgp_prefixlistin = module.params['pn_vrouterbgp_prefixlistin']
	vrouterbgp_prefixlistout = module.params['pn_vrouterbgp_prefixlistout']
	vrouterbgp_reflector = module.params['pn_vrouterbgp_reflector']
	vrouterbgp_capability = module.params['pn_vrouterbgp_capability']
	vrouterbgp_softreconfig = module.params['pn_vrouterbgp_softreconfig']
	vrouterbgp_maxprefix = module.params['pn_vrouterbgp_maxprefix']
	vrouterbgp_maxprefixwarn = module.params['pn_vrouterbgp_maxprefixwarn']
	vrouterbgp_bfd = module.params['pn_vrouterbgp_bfd']
	vrouterbgp_multiprotocol = module.params['pn_vrouterbgp_multiprotocol']
	vrouterbgp_weight = module.params['pn_vrouterbgp_weight']
	vrouterbgp_default = module.params['pn_vrouterbgp_default']
	vrouterbgp_keepalive = module.params['pn_vrouterbgp_keepalive']
	vrouterbgp_holdtime = module.params['pn_vrouterbgp_holdtime']
	vrouterbgp_routemapin = module.params['pn_vrouterbgp_routemapin']
	vrouterbgp_routemapout = module.params['pn_vrouterbgp_routemapout']
	quiet = module.params['pn_quiet']

        if quiet==True:
                cli  = '/usr/bin/cli --quiet --user ' + cliusername + ':' + clipassword + ' '
        else:
                cli = '/usr/bin/cli --quiet --user ' + cliusername + ':' + clipassword + ' '


        if vrouterbgp_name:
                vrouterbgp = cli + vrouterbgp_command + ' vrouter-name ' + vrouterbgp_name

        if vrouterbgp_neighbor:
                vrouterbgp += ' neighbor ' + vrouterbgp_neighbor

        if vrouterbgp_remote_as:
		vrouterbgp += ' remote-as ' + str(vrouterbgp_remote_as)

	if vrouterbgp_nexthop == True:
		vrouterbgp += ' next-hop-self '
        if vrouterbgp_nexthop == False:
		vrouterbgp += ' no-next-hop-self '
 
        if vrouterbgp_password:
                vrouterbgp += ' password ' + vrouterbgp_password

        if vrouterbgp_ebgp:
                vrouterbgp += ' ebgp-multihop ' + str(vrouterbgp_ebgp)

	if vrouterbgp_prefixlistin:
		vrouterbgp += ' prefix-list-in ' + vrouterbgp_prefixlistin

        if vrouterbgp_prefixlistout:
                vrouterbgp += ' prefix-list-out ' + vrouterbgp_prefixlistout

        if vrouterbgp_reflector == True:
                vrouterbgp += ' route-reflector-client '
	if vrouterbgp_reflector == False:
		vroutebgp += ' no-route-reflector-client '

        if vrouterbgp_capability == True:
                vrouterbgp += ' override-capability ' 
	if vrouterbgp_capability == False:
		vrouterbgp += ' no-override-capability '

        if vrouterbgp_softreconfig == True:
                vrouterbgp += ' soft-reconfig-inbound ' 
        if vrouterbgp_softreconfig == False:
                vrouterbgp += ' no-soft-reconfig-inbound '

        if vrouterbgp_maxprefix:
                vrouterbgp += ' max-prefix ' + str(vrouterbgp_maxprefix)

        if vrouterbgp_maxprefixwarn == True:
                vrouterbgp += ' max-prefix-warn-only '
	if vrouterbgp_maxprefixwarn == False:
		vrouterbgp += ' no-max-prefix-warn-only '

        if vrouterbgp_bfd == True:
                vrouterbgp += ' bfd '
	if vrouterbgp_bfd == False:
                vrouterbgp += ' no-bfd '           
 

        if vrouterbgp_multiprotocol:
                vrouterbgp += ' multi-protocol ' + vrouterbgp_multiprotocol

        if vrouterbgp_weight:
                vrouterbgp += ' weight ' + vrouterbgp_weight
	
	if vrouterbgp_default == True:
		vrouterbgp += ' default-originate '
	if vrouterbgp_default == False:
                vrouterbgp += ' no-default-originate '
 
	if vrouterbgp_keepalive:
		vrouterbgp += ' neighbor-keepalive-interval ' + str(vrouterbgp_keepalive)

	if vrouterbgp_holdtime:
		vrouterbgp += ' neighbor-holdtime ' + str(vrouterbgp_holdtime)

	if vrouterbgp_routemapin:
		vrouterbgp += ' route-map-in ' + vrouterbgp_routemapin

	if vrouterbgp_routemapout:
		vrouterbgp += ' route-map-out ' + vrouterbgp_routemapout

        vrouterbgpcmd = shlex.split(vrouterbgp)

        p = subprocess.Popen(vrouterbgpcmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True)
        out,err = p.communicate();

	if out:
        	module.exit_json(
                	vrouterbgpcmd = vrouterbgp,
               		stdout = out.rstrip("\r\n"),
                	changed = True
        	)

	if err:
		module.exit_json(
			vrouterbgpcmd = vrouterbgp,
			stderr = err.rstrip("\r\n"),
			changed = False
		)

from ansible.module_utils.basic import *

if __name__ == '__main__':
        main()
