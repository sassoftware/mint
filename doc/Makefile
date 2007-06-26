#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#

dist_files = Makefile rbuilder.1

all: default-all

install-mkdirs:
	mkdir -p $(DESTDIR)$(mandir)/man1

install: install-mkdirs
	install -m 644 rbuilder.1 $(DESTDIR)$(mandir)/man1

dist: rbuilder.1 default-dist

clean: default-clean

rbuilder.1: rbuilder.1.in ../Makefile
	sed -e s,@version@,$(VERSION),g $< > $@

include ../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
