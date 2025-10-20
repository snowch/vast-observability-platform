# Use CentOS 7 as the base image
FROM centos:7

# Install PostgreSQL 16 and rsyslog
RUN yum update -y && \
    yum install -y https://download.postgresql.org/pub/repos/yum/reporpms/EL-7-x86_64/pgdg-redhat-repo-latest.noarch.rpm && \
    yum install -y postgresql16-server rsyslog && \
    yum clean all

# Initialize the database and set up the data directory
RUN /usr/pgsql-16/bin/postgresql-16-setup initdb
COPY init-scripts/ /docker-entrypoint-initdb.d/

# --- NEW: Copy rsyslog config and entrypoint script ---
COPY rsyslog.conf /etc/rsyslog.conf
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose the PostgreSQL port
EXPOSE 5432

# Set the user to postgres
USER postgres

# --- UPDATED: Use the entrypoint script to start services ---
CMD ["/entrypoint.sh"]
