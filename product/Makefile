#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#

SUBDIRS = content templates datatemplates

python_files = basictroves.py

dist_files = rbuilder.conf httpd.conf

all: default-subdirs

install: install-subdirs pyfiles-install

subdirs: default-subdirs

dist: defaultdist dist-subdirs pyfiles-dist

defaultdist: $(dist_files)
	mkdir -p $(DISTDIR)
	for f in $(dist_files); do \
		cp -a $$f $(DISTDIR); \
	done

pyfiles-dist:
	mkdir -p $(DISTDIR)/$(DIR)
	for f in $(python_files); do \
		cp -a $$f $(DISTDIR)/$(DIR)/$$f; \
	done

pyfiles-install:
	mkdir -p $(DESTDIR)$(mintdir)$(DIR)
	for f in $(python_files); do \
                cp -a $$f $(DESTDIR)$(mintdir)$(DIR)/$$f; \
        done

clean: default-clean clean-subdirs

include ../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
