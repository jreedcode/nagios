#!/usr/bin/python2.6
#
# NAGIOS: check ntp servers sync and interval
# Boolean plugin check

import os
import sys
import subprocess

RESULTS_TEMPLATE = 'NTPD Peer Delta Sync:%ssecs Interval: %ssecs|Interval=%s'
NTP_COMMAND = '/usr/bin/ntpq -p'


def GetPeerInfo(ntp_command):
  """Get informational data from the current peer.

  Args:
    ntp_command: A string of the ntp shell command.
  
  Returns:
    last_sync: An int in seconds since the last sync.
    interval: An int in seconds of the frequency it syncs time.
  """
  try:
    output = subprocess.Popen(ntp_command, shell=True,
                              stdout=subprocess.PIPE).communicate()[0]
  except:
    print 'cannot run ntpq'
    sys.exit(3)

  last_sync = -1
  interval = -1
  for line in output.split('\n'):
    if line.startswith('*'):
      last_sync = line.split()[4]
      interval = line.split()[5]

  if last_sync != -1 and interval != -1:
    return last_sync, interval
  else:
    print 'couldnt determine values'
    sys.exit(1)
 

def main():
  last_sync, interval = GetPeerInfo(NTP_COMMAND)
  results = RESULTS_TEMPLATE % (last_sync, interval, interval)
  print results
  sys.exit(0)


if __name__ == '__main__':
  main()
