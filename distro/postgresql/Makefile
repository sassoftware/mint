#
# Copyright (c) 2008 rPath, Inc.
#
# All Rights Reserved
#

.PHONY: all install $(generated_files)


all: default-all $(generated_files)

install: default-install
	install -D -m0644 postgresql.cron ${DESTDIR}/etc/cron.d/postgresql
	install -D -m0644 postgresql.chkconfig ${DESTDIR}/etc/chkconfig.d/postgresql
	install -D -m0644 postgresql.conf ${DESTDIR}/etc/postgresql.conf.rbuilder
	install -D -m0644 postgresql-rbuilder.chkconfig ${DESTDIR}/etc/chkconfig.d/postgresql-rbuilder
	install -D -m0644 postgresql-rbuilder.sysconfig ${DESTDIR}/etc/sysconfig/pgsql/postgresql-rbuilder
	mkdir -p ${DESTDIR}/etc/init.d
	ln -sf /etc/init.d/postgresql ${DESTDIR}/etc/init.d/postgresql-rbuilder


clean: default-clean


include ../../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
