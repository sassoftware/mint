#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#

.PHONY: all dist install

all: default-all

dist: default-dist

install: default-install
	mkdir -p $(DESTDIR)$(httpddir) $(DESTDIR)$(datadir)/rbuilder
	cp httpd.conf $(DESTDIR)$(httpddir)/rbuilder.conf
	PYTHONPATH=.. python -c "from mint import database; print database.DatabaseTable.schemaVersion" \
			> $(DESTDIR)$(datadir)/rbuilder/schema

clean: default-clean

include ../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
