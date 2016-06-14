#!/usr/bin/python
# Test PN CLI vlan-show

import sys
import subprocess
import shlex
import json


def main():
	module = AnsibleModule(
		argument_spec = dict(
			pn_command = dict(required=True, type='str'),
			pn_options = dict(default=' '),
			pn_quiet = dict(default=True, type='bool')
			),
		supports_check_mode=True
	)

	command = module.params['pn_command']
	options = module.params['pn_options']
	quiet = module.params['pn_quiet']

	if quiet==True:
		vlan = '/usr/bin/cli --quiet ' + command 
	else:
		vlan = '/usr/bin/cli ' + command 


	if options != ' ':
		vlan += ' ' + options

	vlancmd = shlex.split(vlan)
	p = subprocess.Popen(vlancmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True)

	out,err = p.communicate();


	module.exit_json(
		vlancmd = vlan,
		stderr	= err,	
		stdout 	= out,
		changed	= True
	)

from ansible.module_utils.basic import *
#from ansible.module_utils.shell import *

if __name__ == '__main__':
	main()
