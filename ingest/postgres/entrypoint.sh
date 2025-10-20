#!/bin/bash

# Start the rsyslog service
rsyslogd

# Start PostgreSQL in the foreground
exec /usr/pgsql-16/bin/postgres -D "/var/lib/pgsql/16/data"
