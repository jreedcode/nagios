#!/usr/bin/python

"""Read Squid log file data from stdin and save a summary for Nagios."""

import sys
import re
import time
from datetime import datetime
from optparse import OptionParser

RESPONSE_FILE = '/tmp/squid_response'
DATE_MATCHER = (r'([0-9]{2})\/([A-Za-z]{3})\/([0-9]{4}):([0-9]{2}):'
                '([0-9]{2}):([0-9]{2}) ')
# Make sure the system time is set to GMT -5
TZ_MATCHER = r'-0(4|5)00] '
LOG_MATCHER = r'"[A-Z]+ (.+) HTTP/.+" ([0-9]+) [0-9]+ '
IGNORED_DOMAINS = ['']


def MatchString(log_line):
  """Parse the squid log."""
  url, status_code = '', ''
  match = re.search(LOG_MATCHER, log_line)
  if match:
    url = match.group(1)
    status_code = match.group(2)
  return url, status_code


def GetDateSince(log_line):
  """Calculate the time difference between now and the first log entry."""
  url, status_code = '', ''
  matcher = '%s%s%s' % (DATE_MATCHER, TZ_MATCHER, LOG_MATCHER)
  match = re.search(matcher, log_line)
  if match:
    day, month, year, hour, minute, second, url, status_code = match.group(1, 2, 3, 4, 5, 6, 7, 8)
    squid_format = '%Y-%b-%d %H:%M:%S'
    squid_date = datetime.strptime('%s-%s-%s %s:%s:%s' % (year, month, day,
                                                          hour, minute, second),
                                   squid_format)
    date_format = '%Y-%m-%d %H:%M:%S'
    now_date = time.strftime(date_format)
    ending_date = datetime.strptime(now_date, date_format)

    # convert to unix timestamp
    start_date_timestamp = time.mktime(squid_date.timetuple())
    end_date_timestamp = time.mktime(ending_date.timetuple())
    # get minutes
    first_line_date = int(end_date_timestamp - start_date_timestamp) / 60
  else:
    first_line_date  = 'unknown'
  return first_line_date, url, status_code


def SummarizeStatus(failed_urls):
  """Save a report."""
  failing_hostnames = []
  for failed_url in failed_urls:
    failed_domain = ParseDomain(failed_url)
    if failed_domain:
      failing_hostnames.append(failed_domain)

  host_numfailed_dict = {}
  already_counted = []
  for failed_host in failing_hostnames:
    if failed_host in already_counted:
      pass
    else:
      already_counted.append(failed_host)
    bad_reqs_count = failing_hostnames.count(failed_host)
    host_numfailed_dict[failed_host] = bad_reqs_count
  return host_numfailed_dict


def ParseDomain(url):
  """Parse the domain name from the URL."""
  domain = ''
  if url.startswith('http://'):
    domain = url.split('/')[2]
  elif url.startswith('https://'):
    domain = url.split('/')[2]
  elif ':' in url:
    domain = url.split(':')[0]
  # make sure its a url and not an ip address
  if not re.search('[A-Za-z]', domain):
    domain = ''
  # skip an "error" thrown by squid to the client
  if domain == 'error':
    domain = ''
  return domain


def CalculateExitStatus(host_numfailed_dict, warn_threshold, crit_threshold):
  """Determine the exit code for NRPE."""
  exit_status = 0
  for host, fail_num in host_numfailed_dict.iteritems():
    if host not in IGNORED_DOMAINS:
      err_count = int(fail_num)
      if err_count > crit_threshold:
        exit_status = 2
        break
      if err_count > warn_threshold:
        exit_status = 1
  exit_status = str(exit_status)
  return exit_status


def main():
  parser = OptionParser()
  parser.add_option('-w', type='string', dest='warn')
  parser.add_option('-c', type='string', dest='critical')
  (options, _args) = parser.parse_args()
  warn_threshold = int(options.warn)
  crit_threshold = int(options.critical)

  failed_urls = []
  line_counter = 1
  first_line_date = ''
  log_line = sys.stdin.readline().strip()
  while log_line:
    if line_counter == 1:
      first_line_date, url, status_code = GetDateSince(log_line)
    else:
      url, status_code = MatchString(log_line)
    if status_code == '404':
      pass
    elif status_code.startswith('4') or status_code.startswith('5'):
      failed_urls.append(url)
    else:
      # status codes: of 200's, 300's or even just 0
      pass
    line_counter += 1
    log_line = sys.stdin.readline().strip()

  host_numfailed_dict = SummarizeStatus(failed_urls)
  high_low_order = sorted(set(host_numfailed_dict.values()), reverse=True)

  counter = 0
  final_status = []
  duration_string = 'since %s mins ago' % first_line_date
  final_status.append(duration_string)
  for num in high_low_order:
    for host, fail_num in host_numfailed_dict.iteritems():
      if counter > 4:
        break
      if num == fail_num:
        if counter == 0:
          final_status.append('(errors)')
        err_string = '%s (%s)' % (host, fail_num)
        final_status.append(err_string)
        counter += 1

  if len(final_status) == 1:
    final_status.append('No errors')
  with open(RESPONSE_FILE, 'w') as resp_file:
    resp_file.write(', '.join(final_status))
    resp_file.write('\n')
    exit_status = CalculateExitStatus(host_numfailed_dict, warn_threshold,
                                      crit_threshold)
    resp_file.write(exit_status)


if __name__ == '__main__':
  main()
