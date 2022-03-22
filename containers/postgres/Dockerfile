FROM tobi312/rpi-postgresql-postgis
USER postgres
COPY postgresql.conf /etc/postgresql
CMD ["postgres", "-c", "config_file=/etc/postgresql/postgresql.conf"]
