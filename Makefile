#
# Copyright (c) 2005 rPath, Inc.
#

all: subdirs

product=rbuilder
export DESTDIR=
installdir=
export VERSION=2.0.0
export TOPDIR = $(shell pwd)
export DISTDIR = $(TOPDIR)/$(product)$(productqualifier)-$(VERSION)
export prefix = /usr
export sysconfdir = /etc
export servicedir= /srv
export confdir = $(servicedir)/rbuilder/
export datadir = $(prefix)/share
export mandir = $(datadir)/man
export contentdir = $(datadir)/conary/web-common/apps/mint/
export libdir = $(prefix)/lib
export bindir = $(prefix)/bin
export mintdir = $(libdir)/python$(PYVERSION)/site-packages/
export httpddir = $(sysconfdir)/httpd/conf.d/
export maillistdir = /var/mailman
export raapluginsdir = $(libdir)/raa/rPath/

.PHONY: doc

SUBDIRS = mint test scripts raa-plugins commands etc doc 

extra_files = Makefile Make.rules rbuilder.conf httpd.conf

doc_files = NEWS

dist_files = $(extra_files) $(doc_files)

tarball:
	tar cjf $(DISTDIR).tar.bz2 `basename $(DISTDIR)`
	rm -rf $(DISTDIR)

product-dist:
	make -C product DIR=mint/web dist || exit 1;

strip-raa:
	rm -rf $(DISTDIR)/raa-plugins/*
	echo "all: " > $(DISTDIR)/raa-plugins/Makefile
	echo "install: " >> $(DISTDIR)/raa-plugins/Makefile

main-dist: $(dist_files)
	rm -rf $(DISTDIR)
	mkdir $(DISTDIR)
	for d in $(SUBDIRS); do make -C $$d DIR=$$d dist || exit 1; done
	for f in $(dist_files); do \
                mkdir -p $(DISTDIR)/`dirname $$f`; \
                cp -a $$f $(DISTDIR)/$$f; \
	done;

dist: productqualifier=-online
dist: main-dist strip-raa tarball version-file

product: main-dist product-dist tarball version-file

install: all install-subdirs
	mkdir -p $(DESTDIR)$(datadir)/rbuilder/
	mkdir -p $(DESTDIR)$(confdir)
	install -m 644 rbuilder.conf $(DESTDIR)$(confdir)/rbuilder.conf.dist
	sed -i "s,@DESTDIR@,$(installdir),g" $(DESTDIR)$(confdir)/rbuilder.conf.dist
	mkdir -p $(DESTDIR)$(httpddir)
	install httpd.conf $(DESTDIR)$(httpddir)/rbuilder.conf.dist
	sed -i "s,@DATADIR@,$(installdir)$(datadir),g" $(DESTDIR)$(httpddir)/rbuilder.conf.dist
	sed -i "s,@DESTDIR@,$(installdir),g" $(DESTDIR)$(httpddir)/rbuilder.conf.dist

doc:
	PYTHONPATH=.:../conary/: epydoc -o mintdoc mint

version-file:
	if [ -f VERSION ]; then rm -f VERSION; fi
	echo "This is rBuilder $(VERSION)" > VERSION
	echo "(Changeset $(shell hg parents -v | grep changeset | cut -c14-))" >> VERSION

BASEPATH=mintdoc
REMOTEPATH=public_html/
REMOTEHOST=lambchop

sync: doc
	rsync  -a --rsh="ssh" $(BASEPATH) $(REMOTEHOST):$(REMOTEPATH)


clean: clean-subdirs default-clean

subdirs: default-subdirs

include Make.rules

# vim: set sts=8 sw=8 noexpandtab :
