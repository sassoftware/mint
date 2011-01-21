#
# Copyright (c) 2010 rPath, Inc.
#
# All rights reserved.
#

template_files = $(wildcard *.html *.xsl)

all: default-all

install: default-install
	mkdir -p $(DESTDIR)$(PYDIR)/$(PYDEST)
	install -m0644 $(template_files) $(DESTDIR)$(PYDIR)/$(PYDEST)/

clean: default-clean


include ../../../../../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
