#
# Copyright (c) SAS Institute Inc.
#

all: default-all $(generated_files)

install: default-install $(generated_files)
	mkdir -p $(DESTDIR)/usr/share/puppet/modules
	cp -r appengine sasinside-role-master-appengine $(DESTDIR)/usr/share/puppet/modules/
	install -D -m0644 rbuilder.pp $(DESTDIR)/etc/rbuilder.pp

clean: default-clean


include ../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
