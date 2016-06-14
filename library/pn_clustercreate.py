#!/usr/bin/python
# Test PN CLI cluster-create

import sys
import subprocess
import shlex
import json


def main():
	module = AnsibleModule(
		argument_spec = dict(
			pn_clustercommand = dict(required=True, type='str'),
			pn_clustername = dict(required=True, type='str'),
			pn_clusternode1 = dict(required=True, type='str'),
			pn_clusternode2 = dict(required=True, type='str'),	
			pn_clustervalidate = dict(type='bool'),
			pn_quiet = dict(default=True, type='bool')
			)
	)

	clustercommand = module.params['pn_clustercommand']
	clustername = module.params['pn_clustername']
	clusternode1 = module.params['pn_clusternode1']
	clusternode2 = module.params['pn_clusternode2']
	clustervalidate = module.params['pn_clustervalidate']
	quiet = module.params['pn_quiet']

	if quiet==True:
		cli  = "/usr/bin/cli --quiet "
	else:
		cli = "/usr/bin/cli " 
	
	if clustercommand == " ":
		module.fail_json(msg="Invalid command")


	if clustername:
		cluster = cli + clustercommand + ' name ' + clustername

	if clusternode1:
		cluster += ' cluster-node-1 ' + clusternode1
	
	if clusternode2: 
		cluster += ' cluster-node-2 ' + clusternode2

	if clustervalidate==True: 
		cluster += ' validate '
	else:
		cluster += ' no-validate '

	clustercmd = shlex.split(cluster)

	p = subprocess.Popen(clustercmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True)
	out,err = p.communicate();


	module.exit_json(
		clustercmd	= cluster,
		stdout	= out.rstrip("\r\n"),
		stderr	= err.rstrip("\r\n"),	
		changed	= True
	)

from ansible.module_utils.basic import *
#from ansible.module_utils.shell import *

if __name__ == '__main__':
	main()
