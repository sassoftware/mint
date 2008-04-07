#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#

extra_dist = schema.in.py

generated_files = schema custom.cfg rbuilder.conf

.PHONY: all install $(generated_files)


all: default-all $(generated_files)

install: default-install
	# rBuilder config
	install -D -m0644 conaryrc.default $(DESTDIR)/srv/rbuilder/config/conaryrc
	install -D -m0644 rbuilder.conf $(DESTDIR)/srv/rbuilder/config/rbuilder.conf
	touch $(DESTDIR)/srv/rbuilder/config/conaryrc.generated
	echo '# This file will be overwritten by rBuilder first-time setup' \
		> $(DESTDIR)/srv/rbuilder/config/rbuilder-generated.conf
	echo '# Custom configuration overrides for rBuilder may be placed here' \
		> $(DESTDIR)/srv/rbuilder/config/rbuilder-custom.conf
	# rBuilder misc
	install -D -m0644 schema $(DESTDIR)/usr/share/rbuilder/schema
	# rAPA bits
	install -D -m0644 prodlogo.png $(DESTDIR)/usr/share/raa/content/images/prodlogo.png
	install -D -m0644 custom.cfg $(DESTDIR)/etc/raa/custom.cfg
	# system dist (data)
	install -D -m0644 rbuilder.logrotate $(DESTDIR)/etc/logrotate.d/rbuilder
	install -D -m0644 postgres.cron $(DESTDIR)/etc/cron.d/postgres.cron
	install -D -m0644 rbuilder.cron $(DESTDIR)/etc/cron.d/rbuilder.cron
	install -D -m0644 httpd.conf $(DESTDIR)/etc/httpd/conf.d/rbuilder.conf
	# system dist (executable)
	install -D -m0755 rbuilder.tmpwatch $(DESTDIR)/etc/cron.daily/rbuilder.tmpwatch
	install -D -m0755 backup $(DESTDIR)/etc/raa/backup.d/rbuilder-backup
	# chkconfig overrides
	mkdir -p $(DESTDIR)/etc/chkconfig.d
	echo '# chkconfig: 345 23 15' > $(DESTDIR)/etc/chkconfig.d/httpd
	echo '# chkconfig: 345 15 74' > $(DESTDIR)/etc/chkconfig.d/ntpd
	echo '# chkconfig: 345 50 50' > $(DESTDIR)/etc/chkconfig.d/snmpd

clean: default-clean

schema: schema.in.py
	python schema.in.py > schema

custom.cfg: custom.cfg.in
	sed -e s,@VERSION@,$(VERSION), custom.cfg.in > custom.cfg

rbuilder.conf: rbuilder.conf.in
	sed -e s,@VERSION@,$(VERSION), rbuilder.conf.in >rbuilder.conf


include ../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
