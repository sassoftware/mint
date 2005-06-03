#
# Copyright (c) 2005 rpath, Inc.
#

all: subdirs

export VERSION=0.1.0
export TOPDIR = $(shell pwd)
export DISTDIR = $(TOPDIR)/mint-$(VERSION)
export prefix = /usr
export sysconfdir = /etc
export datadir = $(prefix)/share
export contentdir = $(datadir)/conary-web-common/apps/mint/
export libdir = $(prefix)/lib
export mintdir = $(libdir)/python$(PYVERSION)/site-packages/
export httpddir = $(sysconfdir)/httpd/conf.d/

SUBDIRS = mint test

extra_files = Makefile Make.rules mint.conf apache.conf

dist_files = $(extra_files)

dist: $(dist_files)
	rm -rf $(DISTDIR)
	mkdir $(DISTDIR)
	for d in $(SUBDIRS); do make -C $$d DIR=$$d dist || exit 1; done
	for f in $(dist_files); do \
                mkdir -p $(DISTDIR)/`dirname $$f`; \
                cp -a $$f $(DISTDIR)/$$f; \
        done; \
        tar cjf $(DISTDIR).tar.bz2 `basename $(DISTDIR)`
	rm -rf $(DISTDIR)

install: all install-subdirs
	mkdir -p $(DESTDIR)$(mintdir)
	install -m 644 mint.conf $(DESTDIR)$(datadir)/imagetool/
	mkdir -p $(DESTDIR)$(httpddir)
	install httpd.conf $(DESTDIR)$(httpddir)/mint.conf
	sed -i "s,\%DATADIR%,$(datadir),g" $(DESTDIR)$(httpddir)/mint.conf

clean: clean-subdirs default-clean

subdirs: default-subdirs

include Make.rules
