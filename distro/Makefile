#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#

SUBDIRS = artwork postgresql stubs

extra_dist = schema.in.py

generated_files = schema custom.cfg rbuilder.conf

.PHONY: all install $(generated_files)


all: default-all $(generated_files)

install: default-install
	# rBuilder config
	install -D -m0644 conaryrc.default $(DESTDIR)/srv/rbuilder/config/conaryrc
	install -D -m0644 rbuilder.conf $(DESTDIR)/srv/rbuilder/config/rbuilder.conf
	touch $(DESTDIR)/srv/rbuilder/config/conaryrc.generated
	# rBuilder misc
	install -D -m0644 schema $(DESTDIR)/usr/share/rbuilder/schema
	# rAPA bits
	install -D -m0644 prodlogo.png $(DESTDIR)/usr/share/raa/content/images/prodlogo.png
	install -D -m0644 backup.flat $(DESTDIR)/etc/raa/backup.d/rBAFiles
	install -D -m0755 backup.py $(DESTDIR)/etc/raa/backup.d/rbuilder-backup
	install -D -m0644 custom.cfg $(DESTDIR)/etc/raa/custom.cfg
	install -D -m0644 chrootcache.conf $(DESTDIR)/etc/rmake/node.d/chrootcache.conf
	install -D -m0644 collect.flat $(DESTDIR)/etc/raa/collect.d/rBAFiles
	install -D -m0755 collect.sh $(DESTDIR)/etc/raa/collect.d/rBAScript
	install -D -m0644 collectiontool.html $(DESTDIR)/usr/share/raa/content/collectiontool.html
	install -D -m0644 status.html $(DESTDIR)/usr/share/raa/content/status.html
	# rMake node configuration
	install -D -m0644 noderc.main $(DESTDIR)/etc/rmake/node.d/20_rbuilder.conf
	install -D -m0644 serverrc.main $(DESTDIR)/etc/rmake/server.d/20_rbuilder.conf
	# system dist (data)
	install -D -m0644 bootman.conf $(DESTDIR)/etc/bootloader.d/rbuilder.conf
	install -D -m0644 rbuilder.logrotate $(DESTDIR)/etc/logrotate.d/rbuilder
	install -D -m0644 rbuilder.cron $(DESTDIR)/etc/cron.d/rbuilder.cron
	install -D -m0644 httpd.conf $(DESTDIR)/etc/httpd/conf.d/rbuilder-common
	install -D -m0644 httpd-stub.conf $(DESTDIR)/etc/httpd/conf.d/rbuilder.conf
	# system dist (executable)
	install -D -m0755 rbuilder.tmpwatch $(DESTDIR)/etc/cron.daily/rbuilder.tmpwatch
	install -D -m0755 chrootcache.tmpwatch $(DESTDIR)/etc/cron.daily/chrootcache.tmpwatch
	install -D -m0755 rbuilder.init $(DESTDIR)/etc/init.d/rbuilder
	# chkconfig overrides
	mkdir -p $(DESTDIR)/etc/chkconfig.d
	echo '# chkconfig: 345 23 15' > $(DESTDIR)/etc/chkconfig.d/httpd
	echo '# chkconfig: 345 15 74' > $(DESTDIR)/etc/chkconfig.d/ntpd
	echo '# chkconfig: 345 50 50' > $(DESTDIR)/etc/chkconfig.d/snmpd
	# anaconda
	install -D -m0644 anaconda_custom.py $(DESTDIR)/usr/share/anaconda/installclasses/rbuilder.py

clean: default-clean

schema: schema.in.py
	python schema.in.py > schema

custom.cfg: custom.cfg.in
	sed -e s,@VERSION@,$(SHORTVER), custom.cfg.in > custom.cfg

rbuilder.conf: rbuilder.conf.in
	sed -e 's,@VERSION@,$(VERSION),' -e 's,@LIBDIR@,$(LIBDIR),' rbuilder.conf.in >rbuilder.conf


include ../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
