#!/usr/bin/python2.6
#
# 2013

"""Monitor NFS for HADR.

Monitors the SSH process tunneling NFS and the TCP session connecting it to the
remote server.
"""

import sys
import re
import subprocess

TUN_PORT = 49010
RESULTS_TEMPLATE = 'HADR TUNNELS %s:  %s'


def CheckSshProcs():
  """Check if the tunnels are running.
  
  Returns:
    tunnel_pid_list: A list of ints that are PIDs.
  """
  ps_command = '/usr/bin/ps auxww'
  ps_output = subprocess.Popen(ps_command, shell=True,
                               stdout=subprocess.PIPE).communicate()[0]
  tunnel_pid_list = []
  sshd_re = r'^db2inst1 +(?P<tunnel_pid>\d{1,7}) +.*ssh.*%s:.*:2049' % TUN_PORT
  for match in re.finditer(sshd_re, ps_output, re.MULTILINE):
    match_obj = match.groupdict()
    tunnel_pid = '%s' % (match_obj['tunnel_pid'],)
    tunnel_pid_list.append(tunnel_pid)
  return tunnel_pid_list


def CheckTcp():
  """Check if the TCP ports are established on the tunnel.

  Returns:
    tunnel_status: A dict of the tunnel status.
  """
  netstat_command = '/usr/bin/netstat -an | egrep "^tcp4.*%s"' % TUN_PORT
  netstat_output = subprocess.Popen(netstat_command, shell=True,
                                    stdout=subprocess.PIPE).communicate()[0]
  tunnel_status = {'tunnel_up':False}
  src_tun_re = (r'^tcp4 +(\d{1,}) +(\d{1,}) +127.0.0.1.%s +127.0.0.1.'
                '(?P<dst_port>\d{1,}) +ESTABLISHED')
  dst_tun_re = (r'^tcp4 +(\d{1,}) +(\d{1,}) +127.0.0.1.%s +127.0.0.1.'
                '%s +ESTABLISHED')
  for match in re.finditer(src_tun_re % TUN_PORT, netstat_output, re.MULTILINE):
    match_dict = match.groupdict()
    destination_port = '%s' % (match_dict['dst_port'],)
    for line in netstat_output.split('\n'):
      if re.match(dst_tun_re % (destination_port, TUN_PORT), line):
        tunnel_status['tunnel_up'] = True
  return tunnel_status


def main():
  tunnel_pid_list = CheckSshProcs()
  if len(tunnel_pid_list) == 0:
    print RESULTS_TEMPLATE % ('CRITICAL', 'DOWN - NO tunnel process')
    sys.exit(2)
  else:
    tunnel_status = CheckTcp()
    if tunnel_status['tunnel_up'] == True:
      print RESULTS_TEMPLATE % ('OK', 'Up on TCP:%s' % TUN_PORT)
      sys.exit(0)
    else:
      print RESULTS_TEMPLATE % ('CRITICAL', 'DOWN - No tunnel connection')
      sys.exit(2)
 

if __name__ == '__main__':
  main()
