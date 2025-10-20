#!/bin/bash
set -e

# Start rsyslog first, as it needs root privileges.
echo "Starting rsyslogd service..."
rsyslogd

# Use the PGDATA variable, defaulting if not set.
PGDATA="${PGDATA:-/var/lib/pgsql/16/data}"

# Check if the data directory is empty (first run).
if [ -z "$(ls -A "$PGDATA")" ]; then
    echo "Data directory is empty. Initializing PostgreSQL..."

    # Initialize the database cluster as the 'postgres' user.
    su - postgres -c "/usr/pgsql-16/bin/initdb -D $PGDATA"

    # --- FIX: Apply configuration AFTER initdb ---
    echo "Applying custom configuration to postgresql.conf..."
    echo "listen_addresses = '*'" >> "$PGDATA/postgresql.conf"
    echo "shared_preload_libraries = 'pg_stat_statements'" >> "$PGDATA/postgresql.conf"
    echo "pg_stat_statements.track = 'all'" >> "$PGDATA/postgresql.conf"
    echo "pg_stat_statements.max = 10000" >> "$PGDATA/postgresql.conf"

    # Allow password-less local connections for the setup process.
    echo "host all all 127.0.0.1/32 trust" >> "$PGDATA/pg_hba.conf"
    echo "host all all 0.0.0.0/0 md5" >> "$PGDATA/pg_hba.conf"

    # Start a temporary PostgreSQL server to run setup scripts.
    echo "Starting temporary PostgreSQL server..."
    su - postgres -c "/usr/pgsql-16/bin/pg_ctl -D $PGDATA -o \"-c listen_addresses=''\" -w start"

    # Create the main application user and database from environment variables.
    echo "Creating database '$POSTGRES_DB' and user '$POSTGRES_USER'..."
    psql -v ON_ERROR_STOP=1 --username "postgres" <<-EOSQL
        CREATE DATABASE "$POSTGRES_DB";
        CREATE USER "$POSTGRES_USER" WITH PASSWORD '$POSTGRES_PASSWORD';
        GRANT ALL PRIVILEGES ON DATABASE "$POSTGRES_DB" TO "$POSTGRES_USER";
EOSQL

    # Run all custom .sql scripts.
    echo "Running custom init scripts from /docker-entrypoint-initdb.d/..."
    for f in /docker-entrypoint-initdb.d/*.sql; do
        echo "Running script: $f"
        psql -v ON_ERROR_STOP=1 --username "postgres" --dbname "$POSTGRES_DB" < "$f"
    done

    # Stop the temporary server.
    echo "Stopping temporary PostgreSQL server..."
    su - postgres -c "/usr/pgsql-16/bin/pg_ctl -D $PGDATA -w stop"

    # Secure the server by requiring passwords for local connections.
    sed -i "s/host all all 127.0.0.1\/32 trust/host all all 127.0.0.1\/32 md5/" "$PGDATA/pg_hba.conf"

    echo "Initialization complete."
fi

# Start the main PostgreSQL server in the foreground.
echo "Starting PostgreSQL server for general use..."
exec su - postgres -c "/usr/pgsql-16/bin/postgres -D $PGDATA"
