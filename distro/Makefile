#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#

extra_dist = schema.in.py

.PHONY: all install

all: default-all schema

install: default-install all
	install -D -m0644 rbuilder.conf $(DESTDIR)/srv/rbuilder/config/rbuilder.conf
	install -D -m0644 iptables_appliance.conf $(DESTDIR)/etc/firewall
	install -D -m0644 httpd.conf $(DESTDIR)/etc/httpd/conf.d/rbuilder.conf
	install -D -m0644 schema $(DESTDIR)/usr/share/rbuilder/schema

clean: default-clean
	rm -f schema

schema: schema.in.py
	python schema.in.py > schema

include ../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
