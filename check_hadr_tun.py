#!/usr/bin/python2.6
#
# 2013

"""Check the SSH tunnels to it's HADR peers.

Look at the processes controlling the SSH tunnel and report on whether they
appear to be up or down.
"""

import sys
import re
import subprocess

# check the forward tunnel
FWD_SSH_PROC_RE = (r'^db2inst1 +(?P<tunnel_pid>\d{1,7}) '
                    '+.*ssh.*tunnel@HADR_TUN_REMOTE .* 49001:HADR_LOCAL:49001')
# check the reverse tunnel
REV_SSH_PROC_RE = (r'^db2inst1 +(?P<tunnel_pid>\d{1,7}) '
                    '+.*ssh.*tunnel@HADR_TUN_REMOTE .* 49002:HADR_REMOTE:49002')
FWD_TUN_RE = (r'^tcp4 +(\d{1,}) +(\d{1,}) +127.0.0.1.49001 +127.0.0.1.'
              '(?P<dst_port>\d{1,}) +ESTABLISHED')
INVERSE_FWD_TUN_RE = (r'^tcp4 +(\d{1,}) +(\d{1,}) +127.0.0.1.%s +'
                      ' 127.0.0.1.49001 +.*ESTABLISHED')
REV_TUN_RE = r'^tcp4 +(\d{1,}) +(\d{1,}) +127.0.0.1.49002'
RESULTS_TEMPLATE = 'HADR TUNNELS %s:  %s'


def CheckSshProcs():
  """Check if the tunnels are running.
  
  Returns:
    fwd_tunnel_pid_list: A list of ints that are PIDs.
    rev_tunnel_pid_list: A list of ints that are PIDs.
  """
  ps_command = '/usr/bin/ps auxww'
  ps_output = subprocess.Popen(ps_command, shell=True,
                               stdout=subprocess.PIPE).communicate()[0]
  fwd_tunnel_pid_list = []
  rev_tunnel_pid_list = []
  for match in re.finditer(FWD_SSH_PROC_RE , ps_output, re.MULTILINE):
    match_obj = match.groupdict()
    tunnel_pid = '%s' % (match_obj['tunnel_pid'],)
    fwd_tunnel_pid_list.append(tunnel_pid)
  for match in re.finditer(REV_SSH_PROC_RE , ps_output, re.MULTILINE):
    match_obj = match.groupdict()
    tunnel_pid = '%s' % (match_obj['tunnel_pid'],)
    rev_tunnel_pid_list.append(tunnel_pid)

  return fwd_tunnel_pid_list, rev_tunnel_pid_list


def CheckTcp():
  """Check if the TCP ports are actually established on the tunnel.

  Returns:
    up_tuns: A list of tunnels connected.
    down_tuns: A list of tunnels disconnected.
  """
  netstat_command = '/usr/bin/netstat -an | egrep "^tcp4.*4900(1|2)"'
  netstat_output = subprocess.Popen(netstat_command, shell=True,
                                    stdout=subprocess.PIPE).communicate()[0]
  tunnel_statuses = {'forward_tunnel':False,
                     'reverse_tunnel':False}
  for line in netstat_output.split('\n'):
    if re.match(REV_TUN_RE, line):
      tunnel_statuses['reverse_tunnel'] = True
  for match in re.finditer(FWD_TUN_RE, netstat_output, re.MULTILINE):
    match_dict = match.groupdict()
    destination_port = '%s' % (match_dict['dst_port'],)
    for line in netstat_output.split('\n'):
      if re.match(INVERSE_FWD_TUN_RE % destination_port, line):
        tunnel_statuses['forward_tunnel'] = True

  down_tuns = []
  up_tuns = []
  for tun_type, tun_up in tunnel_statuses.iteritems():
    if tun_up == False:
      down_tuns.append(tun_type)
    else:
      up_tuns.append(tun_type)
  return up_tuns, down_tuns


def main():
  fwd_tunnel_pid_list, rev_tunnel_pid_list = CheckSshProcs()
  if len(fwd_tunnel_pid_list) != 1:
    print RESULTS_TEMPLATE % ('CRITICAL', '%d processes for forward tunnel!' %
                              len(fwd_tunnel_pid_list))
    sys.exit(2)
  if len(rev_tunnel_pid_list) != 1:
    print RESULTS_TEMPLATE % ('CRITICAL', '%d processes for reverse tunnel!' %
                              len(rev_tunnel_pid_list))
    sys.exit(2)
  
  up_tuns, down_tuns = CheckTcp()
  if len(up_tuns) >= 2:
    print RESULTS_TEMPLATE % ('OK', ' '.join(up_tuns))
    sys.exit(0)
  else:
    print RESULTS_TEMPLATE % ('CRITICAL', 'Tunnels down - %s' % down_tuns)
    sys.exit(2)
  

if __name__ == '__main__':
  main()
