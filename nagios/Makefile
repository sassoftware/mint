#
# Copyright (c) 2005 rPath, Inc.
#
# All Rights Reserved
#

DESTDIR =
SUBDIRS = mint_nagpy
export TOPDIR = $(shell pwd)
export VERSION = 0.1
export DISTDIR = $(TOPDIR)/mint-nagpy-$(VERSION)
export prefix = /usr
export servicedir= /srv
export libdir = $(prefix)/lib
export libexecdir = $(prefix)/libexec
export sitedir = $(libdir)/python$(PYVERSION)/site-packages
export nagdir = $(sitedir)/mint_nagpy

python_files = check_jobs check_jobserver

extra_dist = Makefile check.cfg Make.rules

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
		tar jcf $(DISTDIR).tar.bz2 `basename $(DISTDIR)`
		rm -rf $(DISTDIR)

install: install-subdirs
		mkdir -p $(DESTDIR)$(servicedir)/rbuilder/nagios
		mkdir -p $(DESTDIR)$(libexecdir)
		install -m 644 check.cfg $(DESTDIR)$(servicedir)/rbuilder/nagios/check.cfg
		install -m 755 check_jobs check_jobserver $(DESTDIR)$(libexecdir)
clean:

include Make.rules

# vim: set sts=8 sw=8 noexpandtab :
