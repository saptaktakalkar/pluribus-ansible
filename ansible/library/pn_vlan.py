#!/usr/bin/python
# Test PN CLI vlan-create/vlan-delete

import sys
import subprocess
import shlex
import json


def main():
	module = AnsibleModule(
		argument_spec = dict(
			pn_vlancommand = dict(required=True, type='str'),
			pn_vlanid = dict(required=True, type='int'),
			pn_quiet = dict(default=True, type='bool')
			)
	)

	vlancommand = module.params['pn_vlancommand']
	vlanid = module.params['pn_vlanid']
	#vlanscope = module.params['pn_vlanscope']
	quiet = module.params['pn_quiet']

	if quiet==True:
		cli  = "/usr/bin/cli --quiet "
	else:
		cli = "/usr/bin/cli " 
	
	if vlancommand == " ":
		module.fail_json(msg="Invalid command")


	if (vlanid<2 | vlanid>4092):
		module.fail_json(msg="Invalid vlan ID")
	vlan = cli + vlancommand + " id " + str(vlanid)

	if vlancommand == "vlan-create":
		vlan += " scope fabric " 

	vlancmd = shlex.split(vlan)
	p = subprocess.Popen(vlancmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True)

	out,err = p.communicate();


	module.exit_json(
		vlancmd	= vlan,
		stdout	= out.rstrip("\r\n"),
		stderr	= err.rstrip("\r\n"),	
		changed	= True
	)

from ansible.module_utils.basic import *
#from ansible.module_utils.shell import *

if __name__ == '__main__':
	main()
