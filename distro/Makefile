#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#

extra_dist = schema.in.py

.PHONY: all install

all: default-all schema

install: default-install all
	# rBuilder config
	install -D -m0644 conaryrc $(DESTDIR)/srv/rbuilder/config/conaryrc
	install -D -m0644 rbuilder.conf $(DESTDIR)/srv/rbuilder/config/rbuilder.conf
	touch $(DESTDIR)/srv/rbuilder/config/conaryrc.generated
	echo '# This file will be overwritten by rBuilder first-time setup' \
		> $(DESTDIR)/srv/rbuilder/config/rbuilder-generated.conf
	echo '# Custom configuration overrides for rBuilder may be placed here' \
		> $(DESTDIR)/srv/rbuilder/config/rbuilder-custom.conf
	# rBuilder misc
	install -D -m0644 schema $(DESTDIR)/usr/share/rbuilder/schema
	# system dist (data)
	install -D -m0644 iptables_appliance.conf $(DESTDIR)/etc/firewall
	install -D -m0644 rbuilder.logrotate $(DESTDIR)/etc/logrotate.d/rbuilder
	install -D -m0644 rbuilder.cron $(DESTDIR)/etc/cron.d/rbuilder.cron
	install -D -m0644 httpd.conf $(DESTDIR)/etc/httpd/conf.d/rbuilder.conf
	# system dist (executable)
	install -D -m0755 rbuilder.tmpwatch $(DESTDIR)/etc/cron.daily/rbuilder.tmpwatch
	# chkconfig overrides
	echo '# chkconfig: 345 23 15' > $(DESTDIR)/etc/chkconfig.d/httpd
	echo '# chkconfig: 345 15 74' > $(DESTDIR)/etc/chkconfig.d/ntpd
	echo '# chkconfig: 345 50 50' > $(DESTDIR)/etc/chkconfig.d/snmpd

clean: default-clean
	rm -f schema

schema: schema.in.py
	python schema.in.py > schema

include ../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
