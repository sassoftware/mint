#
# Copyright (c) 2009 rPath, Inc.
#
# All rights reserved.
#

doc_files = $(wildcard *.txt)

all: default-all

install: default-install
	mkdir -p $(DESTDIR)$(PYDIR)/$(PYDEST)
	find . -name "*.txt" | tar cf - . --files-from=- --no-recursion | tar xf - -C $(DESTDIR)$(PYDIR)/$(PYDEST)
	find $(DESTDIR)$(PYDIR)/$(PYDEST) -type d | xargs chmod 0755
	find $(DESTDIR)$(PYDIR)/$(PYDEST) -type f | xargs chmod 0644

clean: default-clean


include ../../../../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
