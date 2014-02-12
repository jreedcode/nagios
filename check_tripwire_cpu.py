#!/usr/bin/python2.6
#
# NAGIOS: check tripwire process cpu usage
# Boolean plugin check

import os
import sys
import re
import subprocess

PROC_FILE = '/tmp/ps_output'
TRIPWIRE_RE = r'^root +(?P<pid>\d{1,7}) .*tripwire.*jre\/bin\/java'
RESULTS_TEMPLATE = 'Tripwire CPU Usage %s:  %s'
CPU_CRITICAL = 20
CPU_WARNING = 10
PS_COMMAND = '/usr/bin/ps -o cpu -p %s'
CPU_SEARCH_RE = r'(?P<usage>\d{1,})'


def ReadInPsOuput(ps_file):
  """Search for a process in the ps output file.

  Args:
    ps_file: A string of a filename where the processes are stored.

  Returns:
    tripwire_pid: A string of the process id.
  """
  tripwire_pid = ''
  if os.path.exists(ps_file):
    f = open(ps_file)
    for line in f.readlines():
      if re.match(TRIPWIRE_RE, line):
        match_object = re.match(TRIPWIRE_RE, line)
        process = match_object.groupdict()
        tripwire_pid = process['pid']
        break
    f.close()
  return tripwire_pid
 

def CheckTripwireCpu(tripwire_pid):
  """Check the CPU usage on the tripwire java process.

  Args:
    tripwire_pid: A string of the tripwire pid as an int.
  Returns:
    tripwire_cpu: An int of the cpu usage for the tripwire process.
  """
  full_command = PS_COMMAND % tripwire_pid
  ps_output = subprocess.Popen(full_command, shell=True,
                               stdout=subprocess.PIPE).communicate()[0]
  tripwire_proc = False
  for match in re.finditer(CPU_SEARCH_RE, ps_output, re.MULTILINE):
    match_object = match.groupdict()
    tripwire_cpu = int(match_object['usage'])
    tripwire_proc = True
  if tripwire_proc:
    return tripwire_cpu
  else:
    print RESULTS_TEMPLATE % ('CRITICAL', 'No Tripwire process!')
    sys.exit(2)
 

def main():
  tripwire_pid = ReadInPsOuput(PROC_FILE)
  if tripwire_pid:
    tripwire_cpu = CheckTripwireCpu(tripwire_pid)
    if tripwire_cpu > CPU_CRITICAL: 
      print RESULTS_TEMPLATE % ('CRITICAL', '%d|NumOfThreads=%d;%d;%d' %
                                (tripwire_cpu, tripwire_cpu, CPU_WARNING,
                                 CPU_CRITICAL))
      sys.exit(2)
    elif tripwire_cpu > CPU_WARNING: 
      print RESULTS_TEMPLATE % ('WARN', '%d|NumOfThreads=%d;%d;%d' %
                                (tripwire_cpu, tripwire_cpu, CPU_WARNING,
                                 CPU_CRITICAL))
      sys.exit(1)
    else:
      print RESULTS_TEMPLATE % ('OK', '%d|NumOfThreads=%d;%d;%d' %
                                (tripwire_cpu, tripwire_cpu, CPU_WARNING,
                                 CPU_CRITICAL))
      sys.exit(0)
  else:
    print RESULTS_TEMPLATE % ('CRITICAL', 'No Tripwire process!')
    sys.exit(2)


if __name__ == '__main__':
  main()
