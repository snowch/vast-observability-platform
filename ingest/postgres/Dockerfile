# Use CentOS 7 as the base image
FROM centos:7

# Install PostgreSQL 16
RUN yum update -y && \
    yum install -y https://download.postgresql.org/pub/repos/yum/reporpms/EL-7-x86_64/pgdg-redhat-repo-latest.noarch.rpm && \
    yum install -y postgresql16-server && \
    yum clean all

# Initialize the database and set up the data directory
RUN /usr/pgsql-16/bin/postgresql-16-setup initdb
COPY init-scripts/ /docker-entrypoint-initdb.d/

# Expose the PostgreSQL port
EXPOSE 5432

# Set the user to postgres
USER postgres

# Define the command to start the server
CMD ["/usr/pgsql-16/bin/postgres", "-D", "/var/lib/pgsql/16/data"]