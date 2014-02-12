#!/usr/bin/python2.6
#
# 2013

"""Check the HADR log status.

Parse DB2's HADR status command (output as a file) and report on the log file
synchronization and the log buffering (in the case of a secondary system).
"""

import os
import sys
import re

# see this site for a decent explanation of hadr statuses
# http://www.scribd.com/doc/59836598/17/Monitoring-HADR-snapshot

# NAGIOS STUFF
# the command "db2pd -db realtime -hadr" should be output to the status file
STATUS_FILE = '/tmp/hadr_output'
RESULTS_TEMPLATE = 'HADR LOGS %s:  %s'
EXTENDED_STATUS = 'PRIMARY: %s.LOG, STANDBY: %s.LOG, BUFFER: %s'
# REGEXES
ROLE_MATCHER = r'^(?P<role>\w+) +(\w+) +(\w{1,}) +(\d{1,}) +(\d{1,}) '
LOGFILE_MATCHER = r'^(?P<log_file>\w+).LOG +(\d{1,}) +0x(\w{1,})$'
LOG_BUFFER_MATCHER = (r'^(?P<log_file>\w+).LOG +(\d{1,}) +0x.* +'
                      '(?P<percent>\d{1,})%')
BUFFER_THRESHOLD = 50


def ReadStatuses(status_file):
  """Read and parse the HADR status of DB2.
  
  Args:
    command: A string of the filename db2inst1 keeps the hadr status in.

  Returns:
    statuses: A tuple of strings with the log files and buffers used.
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
  
    role_stat = ''
    for match in re.finditer(ROLE_MATCHER, status_string, re.MULTILINE):
      match_dict = match.groupdict()
      role_stat = (match_dict['role'],)
    logs = []
    statuses = ()
    buffer_percent = ()
    if role_stat == 'Primary':
      for match in re.finditer(LOGFILE_MATCHER, status_string, re.MULTILINE):
        match_dict = match.groupdict()
        a_log_file = (match_dict['log_file'],)
        logs.append(a_log_file)
    else:
      for match in re.finditer(LOGFILE_MATCHER, status_string, re.MULTILINE):
        match_dict = match.groupdict()
        a_log_file = (match_dict['log_file'],)
        logs.append(a_log_file)
      for match in re.finditer(LOG_BUFFER_MATCHER, status_string, re.MULTILINE):
        match_dict = match.groupdict()
        a_log_file = '%s' % (match_dict['log_file'],)
        logs.append(a_log_file)
        buffer_percent = (match_dict['percent'],)
    
    if buffer_percent:
      try:
        statuses = ('%s' % logs[0], '%s' % logs[1],
                    '%s' % buffer_percent)
      except:
        return False
    else:
      try:
        statuses = ('%s' % logs[0], '%s' % logs[1], 'N/A')
      except:
        return False

    if len(statuses) == 3:
      return statuses
    else:
      return False
  else:
    return False


def main():
  hadr_statuses = ReadStatuses(STATUS_FILE)
  if hadr_statuses:
    # compare the log files first
    if len(set(hadr_statuses[:2])) != 1:
      primary_log = int(hadr_statuses[0].lstrip('S').rstrip('.LOG'))
      secondary_log = int(hadr_statuses[1].lstrip('S').rstrip('.LOG'))
      if primary_log - secondary_log > 1:
        long_status = EXTENDED_STATUS % hadr_statuses
        print RESULTS_TEMPLATE % ('CRITICAL', long_status)
        sys.exit(2)

    # now check the buffers - secondary side only
    if type(hadr_statuses[2]) is int:
      if int(hadr_statuses[2]) > BUFFER_THRESHOLD:
        long_status = EXTENDED_STATUS % hadr_statuses
        print RESULTS_TEMPLATE % ('CRITICAL', long_status)
        sys.exit(2)
      else:
        long_status = EXTENDED_STATUS % hadr_statuses
        print RESULTS_TEMPLATE % ('OK', long_status)
        sys.exit(0)
    else:
      long_status = EXTENDED_STATUS % hadr_statuses
      print RESULTS_TEMPLATE % ('OK', long_status)
      sys.exit(0)
 
  else:
    print RESULTS_TEMPLATE % ('CRITICAL', 'Cannot read HADR status')
    sys.exit(2)


if __name__ == '__main__':
  main()
