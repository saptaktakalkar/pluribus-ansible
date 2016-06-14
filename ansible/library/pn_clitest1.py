#!/usr/bin/python

# Testing PN CLI Commands


import sys
import shlex
import subprocess

p = subprocess.Popen(["ping -c4 www.google.com"], stdout=subprocess.PIPE, shell=True)
output, err = p.communicate()
print "**** Running command ****\n", output

