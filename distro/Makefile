#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#

extra_dist = schema.in.py

generated_files = schema jobslave_set custom.cfg

.PHONY: all install $(generated_files)


all: default-all $(generated_files)

install: default-install all
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
	install -D -m0644 iptables_appliance.conf $(DESTDIR)/etc/firewall
	install -D -m0644 rbuilder.logrotate $(DESTDIR)/etc/logrotate.d/rbuilder
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
	# freeze jobslave set
	[ -f jobslave_set] && install -D -m0644 jobslave_set $(DESTDIR)/srv/rbuilder/mcp/config.d/jobslave_set

clean: default-clean

schema: schema.in.py
	python schema.in.py > schema

custom.cfg: custom.cfg.in
	sed -e s,@VERSION@,$(VERSION), custom.cfg.in > custom.cfg

jobslave_set:
	if [ -n "$$JOBSLAVE_SET_LABEL" ]; then \
		echo -n 'slaveSetVersion ' >jobslave_set ; \
		conary rq --all-flavors \
			group-jobslave-set=$$JOBSLAVE_SET_LABEL \
			|cut -d = -f 2 |cut -d - -f 1 \
			>>jobslave_set ; \
	fi


include ../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
