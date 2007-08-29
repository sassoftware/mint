#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#

bin_files = \
       rbuilder

all: default-all
	install -D -m 755 rbuilder-wrapper $(TOPDIR)/bin/rbuilder-wrapper
	for f in $(bin_files); do \
		ln -sfn rbuilder-wrapper $(TOPDIR)/bin/$$f; \
	done

install: default-install
	for f in $(bin_files); do \
		install -D -m 755 $$f $(DESTDIR)/usr/bin/$$f; \
	done

clean: default-clean

include $(TOPDIR)/Make.rules
