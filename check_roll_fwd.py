#!/usr/bin/python2.6
#
# 2012

"""Process the db2 automated restore through nagios."""

import os
import sys
import time
import datetime
import re

STATUS_FILE = '/backup/backups/database/restore/roll_fwd.status'
RESULTS_TEMPLATE = 'DB2_ROLL_FWD %s:  %s'
LAST_COMMIT_RE = (r'.*Last committed transaction.* = (?P<year>\d{4})-'
                  '(?P<month>\d{2})-(?P<day>\d{2})-(?P<hour>\d{2})\.'
                  '(?P<minute>\d{2})\.(?P<second>\d{2})\.\d{6} Local')
ROLL_FWD_FILE = '/backup/backups/database/loads/stop_rollforward'
# in minutes
TIME_THRESHOLD = 30


def ReadStatus(status_file):
  """Run the db2 commands and return the time of db roll fwd.
  
  Args:
    command: A string of the filename db2inst1 keeps the roll fwd status in.
  Returns:
    time_to_parse: A tuple of the time from when the last roll fwd happened.
  """
  status_string = ''
  commit_time = False
  if os.path.exists(status_file):
    f = open(status_file)
    for line in f.readlines():
      if line:
        status_string += line
    f.close()
  
    for match in re.finditer(LAST_COMMIT_RE, status_string, re.MULTILINE):
      match_dict = match.groupdict()
      time_to_parse = (int(match_dict['year']),
                       int(match_dict['month']),
                       int(match_dict['day']),
                       int(match_dict['hour']),
                       int(match_dict['minute']),
                       int(match_dict['second']))
      commit_time = True

  if commit_time:
    return time_to_parse
  else:
    return False


def GetTimeDifference(roll_fwd_time):
  """Convert the times to seconds since epoch and return the difference. 

  Args:
    roll_fwd_time: The time of when the roll fwd happened.
  Returns:
    time_diff: A float in minutes between the current time and roll fwd time.
  """
  t = datetime.datetime(roll_fwd_time[0],
                        roll_fwd_time[1],
                        roll_fwd_time[2],
                        roll_fwd_time[3],
                        roll_fwd_time[4],
                        roll_fwd_time[5])
  roll_fwd_since_epoch = time.mktime(t.timetuple())
  time_diff = ((time.time() - roll_fwd_since_epoch) / 60)
  return round(time_diff, 2)


def main():
  roll_fwd_time = ReadStatus(STATUS_FILE)
  if roll_fwd_time:
    time_diff = GetTimeDifference(roll_fwd_time)

    if time_diff > (12 * TIME_THRESHOLD):
      print RESULTS_TEMPLATE % ('CRITICAL', '%d mins old' % time_diff)
      sys.exit(2)
        
    if time_diff > TIME_THRESHOLD:
      if os.path.exists(ROLL_FWD_FILE):
        print RESULTS_TEMPLATE % ('WARN', 'Waiting on CAFs. db2 is %d mins old'
                                  % time_diff)
        sys.exit(1)
      else:
        print RESULTS_TEMPLATE % ('WARN', ('No rollfwd file but db2 is %d '
                                           'mins old') % time_diff)
        sys.exit(1)
    else:
      print RESULTS_TEMPLATE % ('OK', '%d minutes old.' % time_diff)
      sys.exit(0)
  else:
    print RESULTS_TEMPLATE % ('UNKNOWN', 'Cannot determine roll fwd time')
    sys.exit(3)


if __name__ == '__main__':
  main()
