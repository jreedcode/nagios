#!/usr/bin/python2.7
#
# NAGIOS: check ntp server combined offset
# Boolean plugin check

import os
import sys
import re
from optparse import OptionParser
import subprocess

RESULTS_TEMPLATE = 'NTPD Offset %s:  %s'
NTP_COMMAND = '/usr/bin/ntpdc -c loopinfo'
 

def DetermineOffset(ntp_command):
  """Check the CPU usage on the tripwire java process.

  Args:
    ntp_command: A string of the command to get the offset value.
  Returns:
    offset: A float of the combined offset.
  """
  offset = False
  try:
    output = subprocess.Popen(ntp_command, shell=True,
                              stdout=subprocess.PIPE).communicate()[0]
  except:
    print RESULTS_TEMPLATE % ('CRITICAL', 'could not get ntp stats!')
    sys.exit(2)
    
  for line in output.split('\n'):
    if line.startswith('offset'):
      offset = float(line.split()[1])
      if offset == 0.0:
        offset = int(offset) + 0.000001
  return offset
 

def main():
  parser = OptionParser()
  (options, args) = parser.parse_args()
  try:
    warn = int(args[0])
    critical = int(args[1])
  except:
    print 'failed on to parse arguments'
    sys.exit(3)
  if warn < 1 or critical < 1:
    print 'those arguments arent believable'
    sys.exit(3)
    
  offset = DetermineOffset(NTP_COMMAND)

  if offset:
    if offset > critical: 
      print RESULTS_TEMPLATE % ('CRITICAL', '%f|Offset=%f;%d;%d' %
                                (offset, offset, warn, critical))
      sys.exit(2)
    elif offset > warn:
      print RESULTS_TEMPLATE % ('WARN', '%f|Offset=%f;%d;%d' %
                                (offset, offset, warn, critical))
      sys.exit(1)
    else:
      print RESULTS_TEMPLATE % ('OK', '%f|Offset=%f;%d;%d' %
                                (offset, offset, warn, critical))
      sys.exit(0)
  else:
    print RESULTS_TEMPLATE % ('CRITICAL', 'could not get ntp stats!')
    sys.exit(2)


if __name__ == '__main__':
  main()
