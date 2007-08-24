#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#

.PHONY: rbuilder.1

all: default-all rbuilder.1

install: all default-install
	install -D -m 644 rbuilder.1 $(DESTDIR)/usr/share/man/man1/rbuilder.1

clean: default-clean
	rm -f rbuilder.1

rbuilder.1: rbuilder.1.in
	sed -e s,@version@,$(SHORTVER),g $< > $@

include ../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
