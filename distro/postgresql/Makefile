#
# Copyright (c) rPath, Inc.
#

.PHONY: all install $(generated_files)


all: default-all $(generated_files)

install: default-install
	install -D -m0644 custom.conf ${DESTDIR}/srv/rbuilder/config/postgresql-custom.conf
	install -D -m0644 pgbouncer.conf ${DESTDIR}/etc/pgbouncer/pgbouncer.ini
	install -D -m0644 postgresql.cron ${DESTDIR}/etc/cron.d/postgresql
	install -D -m0644 postgresql.conf ${DESTDIR}/usr/share/rbuilder/postgresql.conf
	install -D -m0644 postgresql-rbuilder.sysconfig ${DESTDIR}/etc/sysconfig/pgsql/postgresql-rbuilder
	sed -i "s/@POSTGRES_VERSION@/$(POSTGRES_VERSION)/g" ${DESTDIR}/etc/sysconfig/pgsql/postgresql-rbuilder
	sed -e "s/@POSTGRES_VERSION@/$(POSTGRES_VERSION)/g" meta > $(DESTDIR)/usr/share/rbuilder/postgres-meta
	mkdir -p ${DESTDIR}/etc/rc.d/init.d
	ln -sf /opt/postgresql-$(POSTGRES_VERSION)/etc/init.d/postgresql ${DESTDIR}/etc/rc.d/init.d/postgresql-rbuilder


clean: default-clean


include ../../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
