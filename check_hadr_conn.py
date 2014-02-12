#!/usr/bin/python2.6
#
# 2013

"""Check the HADR connection status.

Parse DB2's HADR status command (output as a file) and report on the State and
Connection Status.
"""

import os
import sys
import re

# see this site for a decent explanation of hadr statuses
# http://www.scribd.com/doc/59836598/17/Monitoring-HADR-snapshot

# NAGIOS STUFF
# the command "db2pd -db realtime -hadr" should be output to the status file
STATUS_FILE = '/tmp/hadr_output'
RESULTS_TEMPLATE = 'HADR_CONNS %s:  %s'
EXTENDED_STATUS = 'ROLE: %s, STATE: %s, STATUS: %s, BYTES BEHIND: %s'
# REGEXES
MAIN_MATCHER = r'^(?P<role>\w+) +(?P<state>\w+) +(\w{1,}) +(\d{1,}) +(?P<bytes>\d{1,}) '
CONNSTAT_MATCHER = r'^(?P<connstat>\w+).*\((\d{1,})\) +(\d{1,})'


def ReadStatuses(status_file):
  """Read and parse the HADR status of DB2.
  
  Args:
    command: A string of the filename db2inst1 keeps the hadr status in.
  Returns:
    statuses: A tuple of strings with role, state, bytes and conn state.
  """
  if os.path.exists(status_file):
    try:
      status_string = ''
      f = open(status_file)
      for line in f.readlines():
        if line:
          status_string += line
      f.close()
    except:
      return False
 
    statuses = ()
    for match in re.finditer(MAIN_MATCHER, status_string, re.MULTILINE):
      match_dict = match.groupdict()
      role_stat = (match_dict['role'],)
      state_stat = (match_dict['state'],)
      bytes_stat = (match_dict['bytes'],)
    for match in re.finditer(CONNSTAT_MATCHER, status_string, re.MULTILINE):
      match_dict = match.groupdict()
      connstat_stat = (match_dict['connstat'],)
    try:
      statuses = ('%s' % role_stat, '%s' % state_stat,
                  '%s' % connstat_stat, '%s' % bytes_stat)
    except:
      return False
    if len(statuses) == 4:
      return statuses
    else:
      return False
  else:
    return False


def main():
  hadr_statuses = ReadStatuses(STATUS_FILE)
  if hadr_statuses:
    # handle the state first
    if hadr_statuses[1] == 'Disconnect':
      x = EXTENDED_STATUS % hadr_statuses
      print RESULTS_TEMPLATE % ('CRITICAL', x)
      sys.exit(2)
    elif hadr_statuses[1] != 'Peer':
      x = EXTENDED_STATUS % hadr_statuses
      print RESULTS_TEMPLATE % ('WARN', x)
      sys.exit(1)
    else:
      # now check connection status
      if hadr_statuses[2] == 'Disconnected':
        x = EXTENDED_STATUS % hadr_statuses
        print RESULTS_TEMPLATE % ('CRITICAL', x)
        sys.exit(2)
      elif hadr_statuses[2] == 'Congested':
        x = EXTENDED_STATUS % hadr_statuses
        print RESULTS_TEMPLATE % ('WARN', x)
        sys.exit(1)
      else:
        x = EXTENDED_STATUS % hadr_statuses
        print RESULTS_TEMPLATE % ('OK', x)
        sys.exit(0)
  else:
    print RESULTS_TEMPLATE % ('CRITICAL', 'Cannot read HADR status')
    sys.exit(2)


if __name__ == '__main__':
  main()
