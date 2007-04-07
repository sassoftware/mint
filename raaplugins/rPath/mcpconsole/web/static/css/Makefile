#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All rights reserved
#

all: default-all default-subdirs

extra_files = Makefile

content_files = mcp.css

dist_files = $(python_files) $(extra_files) $(content_files)

generated_files = *.pyo *.pyc

.PHONY: clean dist install

install: all content-install

content-install:
	mkdir -p $(DESTDIR)$(raapluginsdir)`echo "$(DIR)" | sed "s|/raaplugins\/rPath||"`
	for f in $(content_files); do \
       cp -a $$f $(DESTDIR)$(raapluginsdir)`echo "$(DIR)" | sed "s|/raaplugins\/rPath||"` ;\
	done

dist: default-dist

clean: default-clean clean-subdirs

subdirs: default-subdirs


include ../../../../../../Make.rules
