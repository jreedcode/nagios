#!/usr/bin/python2.6
#
# webify a list of hosts/services which have notifications turned off in nagios.

import time
import re

STATUS_FILE = '/opt/monitor/var/status.log'
OUT_FILE = '/var/www/html/notifications/disabled.txt'
TYPE_MATCHER = r'servicestatus {\n'
HOST_MATCHER = r'\thost_name=(?P<host_name>.*)\n'
DESCRIPTION_MATCHER = r'\tservice_description=(?P<description>.*)\n'
CHECK_MATCHER = r'\tcheck_command=(?P<nagios_command>.*)\n'
NOTIFY_MATCHER = r'\tnotifications_enabled=(?P<notify_bool>[0-1])\n'


def ParseStatus(status_file):
  """Parse the status file for objects with notifications disabled.

  Args:
    status_file: The nagios status log file.

  Returns:
    host_detail_list: A list of host details with notifications disabled.
  """
  host_detail_list = []
  f = open(status_file)
  status_list = f.read().split('\t}')
  for one_item in status_list: # we only need to be concerned with service statuses
    if re.search(TYPE_MATCHER, one_item):
      for match in re.finditer(HOST_MATCHER, one_item, re.MULTILINE):
        match = match.groupdict()
        host_name = match['host_name']
      for match in re.finditer(DESCRIPTION_MATCHER, one_item, re.MULTILINE):
        match = match.groupdict()
        description = match['description']
      for match in re.finditer(CHECK_MATCHER, one_item, re.MULTILINE):
        match = match.groupdict()
        nagios_command = match['nagios_command']
      for match in re.finditer(NOTIFY_MATCHER, one_item, re.MULTILINE):
        match = match.groupdict()
        notify_bool = match['notify_bool']
      if int(notify_bool) == 0:
        host_detail_list.append('%s => %s - %s' % (host_name, nagios_command,
                                                   description))
  f.close()
  host_detail_list.sort()
  return host_detail_list


def WriteOutput(host_detail_list):
  """Write out the results to a text file for the web server to read it.

  Args:
    host_detail_list: A list of host details with notifications disabled.
  """
  out_list = []
  now_time = time.asctime()
  out_list.append('Last updated: %s\n' % now_time)
  for host_item in host_detail_list:
    out_list.append('\n\t%s' % host_item)
  out_str = ''.join(out_list) 
  f = open(OUT_FILE, 'w')
  f.writelines(out_str)
  f.close()
  return


def main():
  host_detail_list = ParseStatus(STATUS_FILE)
  WriteOutput(host_detail_list)


if __name__ == '__main__':
  main()
