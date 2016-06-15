#!/usr/bin/python
# Test PN CLI cluster-delete

import subprocess
import shlex
import json


def main():
	module = AnsibleModule(
		argument_spec = dict(
			pn_clustercommand = dict(required=True, type='str'),
			pn_clustername = dict(required=True, type='str'),
			pn_quiet = dict(default=True, type='bool')
			)
	)

	clustercommand = module.params['pn_clustercommand']
	clustername = module.params['pn_clustername']
	quiet = module.params['pn_quiet']

	if quiet==True:
		cli  = "/usr/bin/cli --quiet "
	else:
		cli = "/usr/bin/cli " 
	
	if clustercommand != "cluster-delete":
		module.fail_json(msg="Invalid command")

	if clustername:
		cluster = cli + clustercommand + ' name ' + clustername

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

if __name__ == '__main__':
	main()
