#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#

SUBDIRS = artwork postgresql stubs platforms project-templates

generated_files = custom.cfg rbuilder.conf

.PHONY: all install $(generated_files)


all: default-all $(generated_files)

install: default-install
	# data directories
	mkdir -p $(DESTDIR)/srv/rbuilder/pki
	# rBuilder config
	install -D -m0644 conaryrc.default $(DESTDIR)/srv/rbuilder/config/conaryrc
	install -D -m0644 rbuilder.conf $(DESTDIR)/srv/rbuilder/config/rbuilder.conf
	sed -i "s/python2.4/python$(PYVER)/g" $(DESTDIR)/srv/rbuilder/config/rbuilder.conf
	touch $(DESTDIR)/srv/rbuilder/config/conaryrc.generated
	install -D -m0644 metadataDescriptor.xml $(DESTDIR)/srv/rbuilder/data/metadataDescriptor.xml
	# rBuilder entitlement
	install -D -m0644 entitlements.xml $(DESTDIR)/etc/conary/entitlements.xml
	# rAPA bits
	install -D -m0644 prodlogo.png $(DESTDIR)/usr/share/raa/content/images/prodlogo.png
	install -D -m0644 backup.flat $(DESTDIR)/etc/raa/backup.d/rBAFiles
	install -D -m0755 backup.py $(DESTDIR)/etc/raa/backup.d/rbuilder-backup
	install -D -m0644 console.msg $(DESTDIR)/etc/raa/console.msg
	install -D -m0644 custom.cfg $(DESTDIR)/etc/raa/custom.cfg
	install -D -m0644 collect.flat $(DESTDIR)/etc/raa/collect.d/rBAFiles
	install -D -m0755 collect.sh $(DESTDIR)/etc/raa/collect.d/rBAScript
	install -D -m0644 collectiontool.html $(DESTDIR)/usr/share/raa/content/collectiontool.html
	install -D -m0644 status.html $(DESTDIR)/usr/share/raa/content/status.html
	# gunicorn
	install -D -m0644 gunicorn.conf $(DESTDIR)/etc/gunicorn.conf
	install -D -m0644 gunicorn.sysconfig $(DESTDIR)/etc/sysconfig/gunicorn
	# nginx
	install -D -m0644 nginx.conf $(DESTDIR)/etc/nginx/nginx.conf
	install -D -m0644 nginx-rbuilder.conf $(DESTDIR)/etc/nginx/conf.d/01_rbuilder.conf
	install -D -m0644 nginx.mime.types $(DESTDIR)/etc/nginx/mime.types
	# rMake node configuration
	install -D -m0644 rmake2/noderc.main $(DESTDIR)/etc/rmake/node.d/20_rbuilder.conf
	install -D -m0644 rmake2/serverrc.main $(DESTDIR)/etc/rmake/server.d/20_rbuilder.conf
	install -D -m0644 rmake2/chrootcache.conf $(DESTDIR)/etc/rmake/node.d/chrootcache.conf
	install -D -m0644 rmake2/clientrc.root $(DESTDIR)/root/.rmakerc
	install -D -m0644 rmake2/server.sysconfig $(DESTDIR)/etc/sysconfig/rmake
	# rmake 3
	install -D -m0644 rmake3/dispatcher.conf $(DESTDIR)/etc/rmake3/server.d/20_rbuilder.conf
	install -D -m0644 rmake3/worker.conf $(DESTDIR)/etc/rmake3/node.d/20_rbuilder.conf
	# system dist (data)
	install -D -m0644 firewall $(DESTDIR)/etc/sysconfig/iptables
	install -D -m0644 firewall6 $(DESTDIR)/etc/sysconfig/ip6tables
	install -D -m0644 rbuilder.logrotate $(DESTDIR)/etc/logrotate.d/rbuilder
	install -D -m0644 rbuilder.cron $(DESTDIR)/etc/cron.d/rbuilder.cron
	# system dist (executable)
	install -D -m0755 rbuilder.tmpwatch $(DESTDIR)/etc/cron.daily/rbuilder.tmpwatch
	install -D -m0755 chrootcache.tmpwatch $(DESTDIR)/etc/cron.daily/chrootcache.tmpwatch
	install -D -m0755 rbuilder.init $(DESTDIR)/etc/rc.d/init.d/rbuilder
	install -D -m0755 rbuilder-authn.init $(DESTDIR)/etc/rc.d/init.d/rbuilder-authn
	install -D -m0755 rbuilder-credstore.init $(DESTDIR)/etc/rc.d/init.d/rbuilder-credstore
	# anaconda
	install -d -m0755 $(DESTDIR)/usr/share/anaconda
	cp -a anaconda/* $(DESTDIR)/usr/share/anaconda/
	# jabberd
	mkdir -p $(DESTDIR)/usr/share/rbuilder/jabberd
	chmod 0750 $(DESTDIR)/usr/share/rbuilder/jabberd
	cp jabberd/*.xml jabberd/db-setup.pgsql $(DESTDIR)/usr/share/rbuilder/jabberd/
	install -D -m0644 jabberd/sysconfig $(DESTDIR)/etc/sysconfig/jabberd
	# amiconfig
	mkdir -p $(DESTDIR)/$(PYDIR)/amiconfig/plugins/
	install -D -m0644 rbuilderstorage.py $(DESTDIR)/$(PYDIR)/amiconfig/plugins/

clean: default-clean

custom.cfg: custom.cfg.in
	sed -e s,@VERSION@,$(SHORTVER), custom.cfg.in > custom.cfg

rbuilder.conf: rbuilder.conf.in
	sed -e 's,@VERSION@,$(VERSION),' -e 's,@LIBDIR@,$(LIBDIR),' rbuilder.conf.in >rbuilder.conf


include ../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
