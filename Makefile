#
# Copyright (c) 2005 rPath, Inc.
#

all: subdirs

product=rbuilder
export DESTDIR=
installdir=
export VERSION=2.1.0
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
export localedir = $(datadir)/locale
export mintdir = $(libdir)/python$(PYVERSION)/site-packages/
export httpddir = $(sysconfdir)/httpd/conf.d/
export maillistdir = /var/mailman
export raapluginsdir = $(libdir)/raa/rPath/

.PHONY: doc

SUBDIRS = mint test scripts raaplugins commands etc doc locales

extra_files = Makefile Make.rules rbuilder.conf httpd.conf

doc_files = NEWS

dist_files = $(extra_files) $(doc_files)

generated_files = VERSION *.tar.bz2

tarball:
	tar cjf $(DISTDIR).tar.bz2 `basename $(DISTDIR)`
	rm -rf $(DISTDIR)

product-dist:
	make -C product DIR=mint/web dist || exit 1;

strip-raa:
	rm -rf $(DISTDIR)/raaplugins/*
	echo "all: " > $(DISTDIR)/raaplugins/Makefile
	echo "install: " >> $(DISTDIR)/raaplugins/Makefile

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
	mkdir -p $(DESTDIR)$(httpddir)
	install httpd.conf $(DESTDIR)$(httpddir)/rbuilder.conf.dist
	sed -i "s,@DATADIR@,$(installdir)$(datadir),g" $(DESTDIR)$(httpddir)/rbuilder.conf.dist
	sed -i "s,@DESTDIR@,$(installdir),g" $(DESTDIR)$(httpddir)/rbuilder.conf.dist
	python -c "from mint import database; print database.DatabaseTable.schemaVersion" > $(DESTDIR)$(datadir)/rbuilder/schema

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

msgcat:
	tg-admin i18n collect

clean: clean-subdirs default-clean

subdirs: default-subdirs

include Make.rules

# vim: set sts=8 sw=8 noexpandtab :
