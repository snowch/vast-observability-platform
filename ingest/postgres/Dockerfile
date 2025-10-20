# Use AlmaLinux 9 as a modern, stable base image
FROM almalinux:9

# Install the official PostgreSQL 16 repository
RUN dnf install -y https://download.postgresql.org/pub/repos/yum/reporpms/EL-9-x86_64/pgdg-redhat-repo-latest.noarch.rpm

# Disable the default PostgreSQL module to prevent conflicts
RUN dnf -qy module disable postgresql

# Install the necessary PostgreSQL packages and rsyslog
RUN dnf install -y postgresql16-server postgresql16-contrib rsyslog && \
    dnf clean all

# Create the data directory and set permissions
RUN mkdir -p /var/lib/pgsql/16/data && \
    chown -R postgres:postgres /var/lib/pgsql/16/data && \
    chmod 700 /var/lib/pgsql/16/data

# --- FIX: REMOVED configuration lines from here ---

# Copy all necessary scripts and configurations
COPY init-scripts/ /docker-entrypoint-initdb.d/
COPY rsyslog.conf /etc/rsyslog.conf
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose the PostgreSQL port
EXPOSE 5432

# Set environment variables to be used by the entrypoint script
ENV PATH=/usr/pgsql-16/bin:$PATH
ENV PGDATA=/var/lib/pgsql/16/data

# Set the entrypoint to our custom script
CMD ["/entrypoint.sh"]
