#!/bin/bash
#
# feed squid logs into the parser

# this requires all of none of the arguments to be set
WARN_THRESHOLD=$1
CRITICAL_THRESHOLD=$2
LINES_TO_COUNT=$3

# set some reasonable defaults
if [ -z $LINES_TO_COUNT ]; then
  LINES_TO_COUNT=20000
fi
if [ -z $WARN_THRESHOLD ]; then
  WARN_THRESHOLD=5
fi
if [ -z $CRITICAL_THRESHOLD ]; then
  CRITICAL_THRESHOLD=10
fi

/usr/bin/tail -"$LINES_TO_COUNT" /var/log/squid/access.log | /usr/lib64/nagios/plugins/parse_squid.py -w $WARN_THRESHOLD -c $CRITICAL_THRESHOLD

if [ -e /tmp/squid_response ]; then
  ret_code=`/usr/bin/tail -1 /tmp/squid_response`
  if [ $ret_code -eq 0 ]; then
    /bin/echo "Squid Proxy OK:  `/usr/bin/head -1 /tmp/squid_response`"
  fi
  if [ $ret_code -eq 1 ]; then
    /bin/echo "Squid Proxy WARN:  `/usr/bin/head -1 /tmp/squid_response`"
  fi
  if [ $ret_code -eq 2 ]; then
    /bin/echo "Squid Proxy CRITICAL:  `/usr/bin/head -1 /tmp/squid_response`"
  fi
  rm -f /tmp/squid_response
  exit $ret_code
else
  /bin/echo "Squid Proxy WARN:  response file not found"
  exit 1
fi
