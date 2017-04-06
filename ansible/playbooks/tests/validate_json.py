#!/usr/bin/python

import json
import sys

fields_to_check = ['task', 'summary', 'msg', 'unreachable', 'exception',
                   'failed', 'changed']

if sys.argv[1]:
    json_file = open(sys.argv[1])
else:
    exit('JSON output file path not provided')

try:
    data = json.load(json_file)
except ValueError:
    exit('Invalid JSON data')

json_data = json.dumps(data)

exit_msg = ''
for field in fields_to_check:
    if field not in json_data:
        exit_msg += '{} is missing from the JSON output'.format(field)

if exit_msg == '':
    print('JSON Validation Successful')
else:
    exit(exit_msg)

