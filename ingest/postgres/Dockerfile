# Use CentOS 7 as the base image
FROM centos:7

# Install PostgreSQL 16 and rsyslog
RUN sed -i 's/mirrorlist/#mirrorlist/g' /etc/yum.repos.d/CentOS-* && \
    sed -i 's|#baseurl=http://mirror.centos.org|baseurl=http://vault.centos.org|g' /etc/yum.repos.d/CentOS-* && \
    yum update -y && \
    yum install -y https://download.postgresql.org/pub/repos/yum/reporpms/EL-7-x86_64/pgdg-redhat-repo-latest.noarch.rpm && \
    yum install -y postgresql16-server rsyslog && \
    yum clean all

# Set the PATH to include PostgreSQL binaries
ENV PATH=/usr/pgsql-16/bin:$PATH

# Initialize the database and set up the data directory
RUN postgresql-16-setup initdb
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
