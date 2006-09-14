#
# Copyright (c) 2005 rPath, Inc.
#
# All Rights Reserved
#

python_files = checkjobs.py checkjobserver.py __init__.py config.py

extra_dist = Makefile 

dist_files = $(python_files) $(extra_dist)

all: default-all default-subdirs

install: default-install

dist: default-dist

mint-nagpy:
		rm -rf $(DISTDIR)
		mkdir $(DISTDIR)
		for d in $(SUBDIRS); do make -C $$d DIR=$$d dist || exit 1; done
		for f in $(dist_files); do \
				mkdir -p $(DISTDIR)/`dirname $$f`; \
				cp -a $$f $(DISTDIR)/$$f; \
		done;

install:
		mkdir -p $(DESTDIR)$(nagdir)
		for f in $(python_files); do \
				install -m 644 $$f $(DESTDIR)$(nagdir); \
		done;
clean: default-clean

include ../Make.rules

# vim: set sts=8 sw=8 noexpandtab :
