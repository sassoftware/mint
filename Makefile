#
# Copyright (c) 2005 rpath, Inc.
#

all: subdirs

export VERSION=0.2.0
export TOPDIR = $(shell pwd)
export DISTDIR = $(TOPDIR)/mint-$(VERSION)
export prefix = /usr
export sysconfdir = /etc
export datadir = $(prefix)/share
export contentdir = $(datadir)/conary/web-common/apps/mint/
export libdir = $(prefix)/lib
export mintdir = $(libdir)/python$(PYVERSION)/site-packages/
export httpddir = $(sysconfdir)/httpd/conf.d/

.PHONY: doc

SUBDIRS = mint test scripts

extra_files = Makefile Make.rules mint.conf httpd.conf

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
	mkdir -p $(DESTDIR)$(datadir)/mint/
	install -m 644 mint.conf $(DESTDIR)$(datadir)/mint/
	mkdir -p $(DESTDIR)$(httpddir)
	install httpd.conf $(DESTDIR)$(httpddir)/mint.conf
	sed -i "s,\%DATADIR%,$(datadir),g" $(DESTDIR)$(httpddir)/mint.conf

doc: 
	PYTHONPATH=.:../conary/: epydoc -o mintdoc mint

BASEPATH=mintdoc
REMOTEPATH=public_html/
REMOTEHOST=lambchop

sync: doc
	rsync  -a --rsh="ssh" $(BASEPATH) $(REMOTEHOST):$(REMOTEPATH)


clean: clean-subdirs default-clean

subdirs: default-subdirs

include Make.rules
