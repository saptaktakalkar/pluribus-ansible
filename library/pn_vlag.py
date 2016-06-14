#!/usr/bin/python
# Test PN CLI vlag-create

import sys
import subprocess
import shlex
import json


def main():
	module = AnsibleModule(
		argument_spec = dict(
			pn_vlagcommand = dict(required=True, type='str'),
			pn_vlagname = dict(required=True, type='str'),
			pn_vlaglport = dict(type='int'),
			pn_vlagpeerport = dict(type='int'),
			pn_vlagmode = dict(type='str'), 
			pn_options = dict(default=' '),
			pn_quiet = dict(default=True, type='bool')
			)
	)

	vlagcommand = module.params['pn_vlagcommand']
	vlagname = module.params['pn_vlagname']
	vlaglport = module.params['pn_vlaglport']
	vlagpeerport = module.params['pn_vlagpeerport']
	vlagmode = module.params['pn_vlagmode']
	options = module.params['pn_options']
	quiet = module.params['pn_quiet']

	if quiet==True:
		vlag = '/usr/bin/cli --quiet ' + vlagcommand 
	else:
		vlag = '/usr/bin/cli ' + vlagcommand 

	if vlagname:
		vlag += ' name ' + vlagname
	else:
                module.fail_json(msg="Failed:Error in vlag name")

	if vlaglport: 
		vlag += ' port ' + str(vlaglport)
	else:
		module.fail_json(msg="Failed:Error in vlag port")

	if vlagpeerport:
		vlag += ' peer-port ' + str(vlagpeerport)
	else:
		module.fail_json(msg="Failed:Error in vlag peer port")

	if vlagmode:
		vlag += ' mode ' + vlagmode
	
	if options!=' ':
		vlag += ' ' + options

	vlagcmd = shlex.split(vlag)
	p = subprocess.Popen(vlagcmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True)

	out,err = p.communicate();


        module.exit_json(
                vlagcmd = vlag,
		stderr = err.rstrip("\r\n"),
		stdout = out.rstrip("\r\n"),
                changed = True
        )
from ansible.module_utils.basic import *
#from ansible.module_utils.shell import *

if __name__ == '__main__':
	main()
