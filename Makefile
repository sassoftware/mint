#
# Copyright (c) 2005 rPath, Inc.
#

all: subdirs

product=mint
export DESTDIR=
installdir=
export VERSION=1.5.4
export TOPDIR = $(shell pwd)
export DISTDIR = $(TOPDIR)/$(product)$(productqualifier)-$(VERSION)
export prefix = /usr
export sysconfdir = /etc
export servicedir= /srv
export confdir = $(servicedir)/mint/
export datadir = $(prefix)/share
export contentdir = $(datadir)/conary/web-common/apps/mint/
export libdir = $(prefix)/lib
export bindir = $(prefix)/bin
export mintdir = $(libdir)/python$(PYVERSION)/site-packages/
export httpddir = $(sysconfdir)/httpd/conf.d/
export maillistdir = /var/mailman

.PHONY: doc

SUBDIRS = mint test scripts mailman

extra_files = Makefile Make.rules mint.conf httpd.conf

doc_files = NEWS

dist_files = $(extra_files) $(doc_files)

tarball:
	tar cjf $(DISTDIR).tar.bz2 `basename $(DISTDIR)`
	rm -rf $(DISTDIR)

product-dist:
	make -C product DIR=mint/web dist || exit 1;

main-dist: $(dist_files)
	rm -rf $(DISTDIR)
	mkdir $(DISTDIR)
	for d in $(SUBDIRS); do make -C $$d DIR=$$d dist || exit 1; done
	for f in $(dist_files); do \
                mkdir -p $(DISTDIR)/`dirname $$f`; \
                cp -a $$f $(DISTDIR)/$$f; \
	done;

dist: productqualifier=-online
dist: main-dist tarball

product: main-dist product-dist tarball

install: all install-subdirs
	mkdir -p $(DESTDIR)$(datadir)/mint/
	mkdir -p $(DESTDIR)$(confdir)
	install -m 644 mint.conf $(DESTDIR)$(confdir)/mint.conf.dist
	sed -i "s,@DESTDIR@,$(installdir),g" $(DESTDIR)$(confdir)/mint.conf.dist
	mkdir -p $(DESTDIR)$(httpddir)
	install httpd.conf $(DESTDIR)$(httpddir)/mint.conf.dist
	sed -i "s,@DATADIR@,$(installdir)$(datadir),g" $(DESTDIR)$(httpddir)/mint.conf.dist
	sed -i "s,@DESTDIR@,$(installdir),g" $(DESTDIR)$(httpddir)/mint.conf.dist

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

# vim: set sts=8 sw=8 noexpandtab :
