#
# Copyright (c) 2009 rPath, Inc.
#
# All rights reserved.
#

doc_files = $(wildcard *.txt)

all: default-all

install: default-install
	mkdir -p $(DESTDIR)$(PYDIR)/$(PYDEST)
	install -m0644 $(doc_files) $(DESTDIR)$(PYDIR)/$(PYDEST)/

clean: default-clean


include ../../../../../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
