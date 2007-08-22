#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#

.PHONY: rbuilder.1

dist_files = Makefile rbuilder.1.in

all: default-all rbuilder.1

dist: default-dist

install: all default-install
	install -D -m 644 rbuilder.1 $(DESTDIR)$(mandir)/man1/rbuilder.1

clean: default-clean
	rm rbuilder.1

rbuilder.1: rbuilder.1.in
	sed -e s,@version@,$(SHORTVER),g $< > $@

include ../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
