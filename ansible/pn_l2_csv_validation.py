#!/usr/bin/python

"""
This python script is to validate L2 VRRP csv file.

Sample CSV file row:
# VRRP IP, VLAN ID, ACTIVE SWITCH
101.108.102.0/24, 102, gui-spine1

Example Usage:
python pn_l2_csv_validation.py l2_csv_file.csv

"""

import csv
import socket
import sys

if len(sys.argv) != 2:
    msg = 'Execution Error: Please provide csv file name!\n'
    msg += 'Example usage: python pn_l2_csv_validation.py l2_csv_file.csv'
    exit(msg)

msg = ''
line_count = 0

reader = csv.reader(open(sys.argv[1]))
for csv_line in reader:
    line_count += 1
    if csv_line[0].startswith('#'):
        # Skip comments which starts with '#'
        continue
    else:
        # Check length of line.
        if len(csv_line) != 3:
            msg += 'Invalid line length at line number {}\n'.format(line_count)
        else:
            ip = csv_line[0].replace(' ', '')
            vlan = csv_line[1].replace(' ', '')
            switch = csv_line[2].replace(' ', '')

            if not ip or not vlan or not switch:
                msg += 'Invalid entry at line number {}\n'.format(line_count)
            else:
                try:
                    # IP address validation
                    ip = str(ip)
                    if '/' not in ip:
                        raise socket.error
                    else:
                        address = ip.split('/')
                        socket.inet_aton(address[0])
                        if not address[1].isdigit():
                            raise socket.error

                except socket.error:
                    msg += 'Invalid IP {} at line number {}\n'.format(
                        ip, line_count
                    )

                # Vlan ID validation
                if not vlan.isdigit():
                    msg += 'Invalid VLAN ID {} at line number {}\n'.format(
                        vlan, line_count
                    )

                # Switch name validation
                if switch.isdigit():
                    msg += 'Invalid SWITCH NAME {} at line number {}\n'.format(
                        switch, line_count
                    )

if msg:
    exit(msg)
else:
    exit('Valid csv file')

