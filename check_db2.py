#!/usr/bin/python2.6
#
# 2013

"""A DB2 checking plugin for nagios.

A modular plugin to enable checking of DB2 values from data stored DB2 database
called db2mond. You need the db2 python libraries ibm_db.
"""

import os
import sys
import ConfigParser
import ibm_db
from optparse import OptionParser

RESULTS_TEMPLATE = 'DB2 %s:  %s'


def ReadCredentials():
  """Read credentials from a file."""
  try:
    cred_instance = ConfigParser.ConfigParser()
    cred_instance.readfp(open('/etc/nagios_mond.passwd'))
  except Exception, e:
    print RESULTS_TEMPLATE % ('UNKNOWN', 'could not read credentials')
    sys.exit(3)
  else:
    username = cred_instance.get('db2_mond_auth', 'user')
    password = cred_instance.get('db2_mond_auth', 'password')
  return username, password


def GetValidMonitoring():
  """Get the available monitorable values from mond.
 
  Returns:
    mon_list: A list of tuples containing monitoring values and thresholds.
  """
  username, password = ReadCredentials()
  sql = """select * from MONITOR.DB2MON_MONITOR"""
  try:
    conn = ibm_db.connect('db2mond', username, password)
    statement = ibm_db.exec_immediate(conn, sql)
  except Exception, e:
    print RESULTS_TEMPLATE % ('UNKNOWN', 'Database connect error.')
    sys.exit(3)

  results_tuple = ibm_db.fetch_tuple(statement)
  mon_list = []
  while results_tuple != False:
    mon_list.append(results_tuple)
    results_tuple = ibm_db.fetch_tuple(statement)
  ibm_db.close(conn)

  return mon_list


def UpdateChecks(actual_value, args_list, mon_list):
  """Update the actual value and timestamp of the node/sp results.

  Args:
    actual_value: An int of the value of whats being checked.
    args_list: A list of stored procedure arguments.
    mon_list: A list of tuples containing monitoring values and thresholds.
  """
  username, password = ReadCredentials()
  try:
    conn = ibm_db.connect('db2mond', username, password)
  except Exception, e:
    print RESULTS_TEMPLATE % ('UNKNOWN', 'could not connect to DB2mond')
    sys.exit(3)
 
  statement = False
  if len(args_list) == 3:
    for row_item in mon_list:
      if (args_list[0] == row_item[0] and args_list[1] == row_item[4] and
          args_list[2] == row_item[2]):
        sql = """update MONITOR.DB2MON_MONITOR set DB_MON_VALUE = '%s',
                 DB_MON_TIME = current timestamp where DB_NODE_ID = '%s'
                 and DB_MON_SP_NAME = '%s' and DB_MON_SUB_ID = '%s'"""
        full_sql = sql % (actual_value, args_list[0], args_list[1],
                          args_list[2])
        statement = ibm_db.exec_immediate(conn, full_sql)
        break
  elif len(args_list) == 2:
    for row_item in mon_list:
      if args_list[0] == row_item[0] and args_list[1] == row_item[4]:
        sql = """update MONITOR.DB2MON_MONITOR set DB_MON_VALUE = '%s',
                 DB_MON_TIME = current timestamp where DB_NODE_ID = '%s'
                 and DB_MON_SP_NAME = '%s'"""
        full_sql = sql % (actual_value, args_list[0], args_list[1])
        statement = ibm_db.exec_immediate(conn, full_sql)
        break
 
  # store the status for debugging
  if statement:
    num_of_updates = ibm_db.num_rows(statement)
    if num_of_updates > 0:
      update_status = 'success'
  else:
    update_status = 'failed'

  ibm_db.close(conn)
  return


def CheckValidArgs(mon_list, args_list):
  """Verify the arguments passed are something valid to check.

  Args:
    mon_list: A list of tuples containing monitoring values and thresholds.
    args_list: A list of arugments passed to nagios.

  Returns:
    args_status: A string of the status of the arg parsing.
  """
  valid_nodes = [node[0] for node in mon_list]
  valid_mon_types = [mon_type[4] for mon_type in mon_list]
  if args_list[0] not in valid_nodes or args_list[1] not in valid_mon_types:
    args_status = 'Monitoring data not found'
  else:
    args_status = 'OK'
  return args_status


def GetStoredProcResult(args_list):
  """Get the results from running the stored proc.

  Args:
    args_list: A list of stored procedure arguments.
  
  Returns:
    actual_value: An int of the stored proc result.
  """
  # initialize the return values
  x_val, y_val = 0, 0
  stored_proc = '%s' % args_list[1]
  if len(args_list) == 2:
    sp_args_tuple = (args_list[0], x_val, y_val)
    return_key = 2
  else:
    sp_args_tuple = (args_list[0], args_list[2], x_val, y_val)
    return_key = 3
 
  username, password = ReadCredentials()
  try:
    conn = ibm_db.connect('db2mond', username, password)
    results_tuple = ibm_db.callproc(conn, stored_proc, sp_args_tuple)
  except Exception, e:
    print str(e)
    print RESULTS_TEMPLATE % ('UNKNOWN', 'could not connect to DB2mond')
    sys.exit(3)
 
  actual_value = results_tuple[return_key]
  ibm_db.close(conn)
  return int(actual_value)
 
 
def CompareActualWithThreshold(actual_value, args_list, mon_list):
  """Compare the actual value against it's threshold.

  Args:
    actual_value: An int of the value of whats being checked.
    args_list: A list of stored procedure arguments.
    mon_list: A list of tuples containing monitoring values and thresholds.

  Returns:
    status_str: A string of the plugin return status.
    description: A string describing the results of the stored proc.
    thresholds_list: A list of values storing warning and critical values.
  """
  if len(args_list) == 3:
    thresholds_list = []
    for row_item in mon_list:
      if (args_list[0] == row_item[0] and args_list[1] == row_item[4] and
          args_list[2] == row_item[2]):
        description = row_item[3]
        thresholds_list.append(str(row_item[5]))
        thresholds_list.append(str(row_item[6]))
        if actual_value > int(row_item[6]):
          status_str = 'CRITICAL'
        elif actual_value > int(row_item[5]):
          status_str = 'WARNING'
        else:
          status_str = 'OK'
        break
  elif len(args_list) == 2:
    thresholds_list = []
    for row_item in mon_list:
      if args_list[0] == row_item[0] and args_list[1] == row_item[4]:
        description = row_item[3]
        thresholds_list.append(str(row_item[5]))
        thresholds_list.append(str(row_item[6]))
        if actual_value > int(row_item[6]):
          status_str = 'CRITICAL'
        elif actual_value > int(row_item[5]):
          status_str = 'WARNING'
        else:
          status_str = 'OK'
        break
  else:
    print RESULTS_TEMPLATE % ('UNKNOWN', 'Could not compare values')
    sys.exit(3)

  return status_str, description, thresholds_list
 

def main():
  usage= """
    %prog NODE!MONITOR![SUB_MONITOR]

    You should supply 2 or 3 arguments depending on your command.
      Node: The node name of the system.
      Monitor: The type of monitoring to do (stored proc name).
      Sub Monitor: Optional. The sub-type monitoring. AKA stored proc argument.
  """
  parser = OptionParser(usage=usage)
  (options, args) = parser.parse_args()
  args_list = [user_arg.upper() for user_arg in args]
  if 'IGNORE' in args_list:
    args_list.remove('IGNORE')
 
  if len(args_list) < 2:
    print RESULTS_TEMPLATE % ('UNKNOWN', 'Cannot check %s' % args_list)
    sys.exit(3)

  mon_list = GetValidMonitoring()
  args_status = CheckValidArgs(mon_list, args_list)
  if args_status != 'OK':
    print RESULTS_TEMPLATE % ('UNKNOWN', 'Cannot check %s' % args_list)
    sys.exit(3)

  if len(args_list) == 3:
    # attempt a check with a sub type 
    actual_value = GetStoredProcResult(args_list)
  elif len(args_list) == 2:
    # attempt a single check
    actual_value = GetStoredProcResult(args_list)
  else:
    print RESULTS_TEMPLATE % ('UNKNOWN', 'Cannot process arguments')
    sys.exit(3)

  status_str, description, thresholds_list = (
    CompareActualWithThreshold(actual_value, args_list, mon_list))
 
  UpdateChecks(actual_value, args_list, mon_list)
  if len(args_list) == 3:
    actual_value = '%d%%|percent=%s;%s' % (actual_value, actual_value,
                                           ';'.join(thresholds_list))
  else:
    actual_value = '%d|Total=%s;%s' % (actual_value, actual_value,
                                       ';'.join(thresholds_list))

  # print the template and exit
  print RESULTS_TEMPLATE % (status_str, '%s reports %s' % (description,
                                                           actual_value))
  if status_str == 'CRITICAL':
    sys.exit(2)
  elif status_str == 'WARNING':
    sys.exit(1)
  else:
    sys.exit(0)


if __name__ == '__main__':
  main()
