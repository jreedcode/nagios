#!/usr/bin/python2.6
#
# Nov 2013: Nagios db2 logging file check

"""Verify DB2 archive log file age.

This calculates how quickly database log files are being created. If the rate is
too fast then a chance exists for the drive space to be exauhsted. If it too
slow, then the database might be seeing low transaction volume. This is mostly
just informational but it will give infrastructure staff a good baseline of the
transaction to log file population ratio.
"""

import os
import sys
import time
import re
import platform
import optparse

LOG_FILE_MATCHER = r'S(?P<incrementor>\d{7}).LOG'
# this var needs changing for your setup
HOSTNAME_PATH_DICT = {
  'mach_name':'unix_path_to_archived_logs',
  'mach_name':'unix_path_to_archived_logs'}
# make sure this has 3 values
HRS_TO_TRACK = [4, 12, 24]
OUTPUT_TEMPLATE = ('%s - average %dhr DB2 archive log creation age: %s mins'
                   '|%dhr-avg=%s; %dhr-avg=%s; %dhr-avg=%s;')


def CheckFiles(path):
  """Determine the average time between log files.

  Args:
    path: A string of the current archive log path.

  Returns:
    average_mins_tuple: A tuple of ints for the hours being tracked.
  """
  one_day_secs = 60 * 60 * HRS_TO_TRACK[2]
  half_day_secs = 60 * 60 * HRS_TO_TRACK[1]
  four_hr_secs = 60 * 60 * HRS_TO_TRACK[0]
  now_secs = int(time.time())
  day_times, half_day_times, four_hr_times = [], [], []

  for log_file in os.listdir(path):
    if re.match(LOG_FILE_MATCHER, log_file):
      mod_time = int(os.stat('%s/%s' % (path, log_file)).st_mtime)
      if mod_time > (now_secs - one_day_secs):
        day_times.append(mod_time)
      if mod_time > (now_secs - half_day_secs):
        half_day_times.append(mod_time)
      if mod_time > (now_secs - four_hr_secs):
        four_hr_times.append(mod_time)

  if len(day_times) > 1:
    day_averages = []
    for i in range(0, (len(day_times) - 1)):
      one_time, two_time = day_times[i:(i+2)]
      time_diff = two_time - one_time
      day_averages.append(time_diff)
    average_secs = sum(day_averages) / len(day_averages)
    day_avg = average_secs / 60
  elif len(day_times) == 1:
    day_avg = day_times[0]
  else:
    day_avg = 0

  if len(half_day_times) > 1:
    half_day_averages = []
    for i in range(0, (len(half_day_times) - 1)):
      one_time, two_time = half_day_times[i:(i+2)]
      time_diff = two_time - one_time
      half_day_averages.append(time_diff)
    average_secs = sum(half_day_averages) / len(half_day_averages)
    half_day_avg = average_secs / 60
  elif len(half_day_times) == 1:
    half_day_avg = half_day_times[0]
  else:
    half_day_avg = 0

  if len(four_hr_times) > 1:
    four_hr_averages = []
    for i in range(0, (len(four_hr_times) - 1)):
      one_time, two_time = four_hr_times[i:(i+2)]
      time_diff = two_time - one_time
      four_hr_averages.append(time_diff)
    average_secs = sum(four_hr_averages) / len(four_hr_averages)
    four_hr_avg = average_secs / 60
  elif len(four_hr_times) == 1:
    four_hr_avg = day_times[0]
  else:
    four_hr_avg = 0

  average_mins_tuple = (day_avg, half_day_avg, four_hr_avg)
  return average_mins_tuple


def FindRecentLogPath(log_path_root):
  """Find the currently used active db2 log path.
  
  Args:
    log_path_root: A string of the archive log path root.

  Returns:
    current_archive_path: A string of the currently used archive log directory.
  """
  log_directories = os.listdir(log_path_root)
  mtimes_dir_dict = {}
  for directory in log_directories:
    stat_data = os.stat('%s/%s' % (log_path_root, directory))
    mtimes_dir_dict[stat_data.st_mtime] = directory

  most_recent_mtime = max(mtimes_dir_dict.keys())
  current_archive_path = '%s/%s' % (log_path_root.rstrip('/'),
                                    mtimes_dir_dict[most_recent_mtime])
  return current_archive_path


def main():
  parser = optparse.OptionParser()
  parser.add_option('-w', '--warn', type='int', dest='warn')
  parser.add_option('-c', '--critical', type='int', dest='critical')
  (options, args) = parser.parse_args()
  if not options.warn or not options.critical:
    parser.error('Warn or critical values invalid. Use "-h" for help.')

  my_name = platform.node().lower()
  if my_name in HOSTNAME_PATH_DICT.keys():
    path = HOSTNAME_PATH_DICT[my_name]
    current_archive_path = FindRecentLogPath(path)
    average_mins_tuple = CheckFiles(current_archive_path)
  else:
    parser.error('Your hostname is missing from the plugin!.')

  if average_mins_tuple[0] < options.critical:
    print OUTPUT_TEMPLATE % ('CRITICAL', min(HRS_TO_TRACK),
                             average_mins_tuple[0],
                             HRS_TO_TRACK[0], average_mins_tuple[0], 
                             HRS_TO_TRACK[1], average_mins_tuple[1],
                             HRS_TO_TRACK[2], average_mins_tuple[2])
    sys.exit(2)
  elif average_mins_tuple[0] < options.warn:
    print OUTPUT_TEMPLATE % ('WARN', min(HRS_TO_TRACK), average_mins_tuple[0],
                             HRS_TO_TRACK[0], average_mins_tuple[0], 
                             HRS_TO_TRACK[1], average_mins_tuple[1],
                             HRS_TO_TRACK[2], average_mins_tuple[2])
    sys.exit(1)
  else:
    print OUTPUT_TEMPLATE % ('OK', min(HRS_TO_TRACK), average_mins_tuple[0],
                             HRS_TO_TRACK[0], average_mins_tuple[0], 
                             HRS_TO_TRACK[1], average_mins_tuple[1],
                             HRS_TO_TRACK[2], average_mins_tuple[2])
    sys.exit(0)


if __name__ == '__main__':
  main()
