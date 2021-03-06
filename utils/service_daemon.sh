#!/bin/sh
### BEGIN INIT INFO
# Provides:          btt_service
# Required-Start:    $local_fs $network $time $syslog
# Required-Stop:     $local_fs $network $time $syslog
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Description:       Buildtime Trend as a Service daemon
### END INIT INFO

SCRIPT='python /vagrant/service.py'

PIDFILE=/tmp/btt_service.pid
LOGFILE=/var/log/btt_service.log

start() {
  if [ -f $PIDFILE ] && kill -0 $(cat $PIDFILE); then
    echo 'Service already running' >&2
    return 1
  fi
  echo 'Starting service...' >&2
  `$SCRIPT` &
  echo 'Service started' >&2
}

stop() {
  if [ ! -f "$PIDFILE" ] || ! kill -0 $(cat "$PIDFILE"); then
    echo 'Service not running' >&2
    return 1
  fi
  echo 'Stopping service...' >&2
  kill -15 $(cat "$PIDFILE")
  echo 'Service stopped' >&2
}

case "$1" in
  start)
    start
    ;;
  stop)
    stop
    ;;
  restart)
    stop
    start
    ;;
  *)
    echo "Usage: $0 {start|stop|restart}"
esac
