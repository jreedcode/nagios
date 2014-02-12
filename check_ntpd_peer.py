#!/usr/bin/python2.7
#
# NAGIOS: check ntp servers offset
# Boolean plugin check

import os
import sys
import socket
import subprocess

RESULTS_TEMPLATE = 'NTPD Peer %s:  %s'
STATS_FILE = '/var/log/ntpstats/peerstats'

POOL_NAMES = ('ca.pool.ntp.org', '3.debian.pool.ntp.org',
              '2.debian.pool.ntp.org', '1.debian.pool.ntp.org',
              '0.debian.pool.ntp.org', 'pool.ntp.org')
 

def GetPoolServerInfo(stats_file):
  """Get the pool server info that is it's current peer.

  Args:
    stats_file: A string of the file name where stats are kept.

  Returns:
    pool_name: A string of the peer's server name.
    peer_offset: A float of the peer's offset.
  """
  pool_name = ''
  peer_ip = ''
  peer_offset = 0.0
  f = open(stats_file)
  for line in f:
    pass
  peer_ip = line.split()[2]
  peer_offset = float(line.split()[4])
 
  if peer_ip:
    pool_name = GetPoolName(peer_ip)
  else:
    print 'cannot resolve peer name1'
    sys.exit(3)
   
  if not pool_name:
    try:
      pool_name, dunno, ip = socket.gethostbyaddr(peer_ip)
    except socket.herror:
      pool_name = 'NODNSNAME'
    except Exception, err:
      pool_name = False
      
  return pool_name, peer_offset
 

def GetPoolName(ip):
  """Get the reverse lookup of the ip in the pool.

  Args:
    ip: A string of an IP address.

  Returns:
    pool_name: A string of the fqdn.
  """
  for pool_name in POOL_NAMES:
    query, aliases, ip_list = socket.gethostbyname_ex(pool_name)
    if ip in ip_list:
      return pool_name


def main():
  pool_name, offset = GetPoolServerInfo(STATS_FILE)
  if pool_name:
    print RESULTS_TEMPLATE % ('OK', 'Peer: %s  Offset:%f|Offset=%f' %
                              (pool_name, offset, offset))
    sys.exit(0)
  else:
    print RESULTS_TEMPLATE % ('WARN', 'Not peered with any pool server!')
    sys.exit(1)


if __name__ == '__main__':
  main()
