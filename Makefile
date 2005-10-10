#
# Copyright (c) 2005 rPath, Inc.
#

all: subdirs

DESTDIR=$(installdir)
export DESTDIR=$(DESTDIR)
export VERSION=0.6.0
export TOPDIR = $(shell pwd)
export DISTDIR = $(TOPDIR)/mint-$(VERSION)
export prefix = /usr
export sysconfdir = /etc
export servicedir= /srv
export confdir = $(servicedir)/mint/
export datadir = $(prefix)/share
export contentdir = $(datadir)/conary/web-common/apps/mint/
export libdir = $(prefix)/lib
export mintdir = $(libdir)/python$(PYVERSION)/site-packages/
export httpddir = $(sysconfdir)/httpd/conf.d/
export maillistdir = /var/mailman

.PHONY: doc

SUBDIRS = mint test scripts mailman

extra_files = Makefile Make.rules mint.conf httpd.conf authrepo.cnr

doc_files = NEWS TODO

dist_files = $(extra_files) $(doc_files)

tarball:
	tar cjf $(DISTDIR).tar.bz2 `basename $(DISTDIR)`
	rm -rf $(DISTDIR)

product-dist:
	echo $(OVERRIDEME)
	exit 1
	make -C product DIR=mint/web dist || exit 1;

main-dist: $(dist_files)
	rm -rf $(DISTDIR)
	mkdir $(DISTDIR)
	for d in $(SUBDIRS); do make -C $$d DIR=$$d dist || exit 1; done
	for f in $(dist_files); do \
                mkdir -p $(DISTDIR)/`dirname $$f`; \
                cp -a $$f $(DISTDIR)/$$f; \
	done;

dist: main-dist tarball
product: main-dist product-dist tarball

install: all install-subdirs
	mkdir -p $(DESTDIR)$(datadir)/mint/
	mkdir -p $(DESTDIR)$(confdir)
	install -m 644 mint.conf $(DESTDIR)$(confdir)/mint.conf.dist
	sed -i "s,@DESTDIR@,$(installdir),g" $(DESTDIR)$(confdir)/mint.conf.dist
	if [ ! -e $(DESTDIR)$(confdir)/mint.conf ]; then \
		cp -a $(DESTDIR)$(confdir)/mint.conf.dist $(DESTDIR)$(confdir)/mint.conf; \
	fi
	mkdir -p $(DESTDIR)$(httpddir)
	install httpd.conf $(DESTDIR)$(httpddir)/mint.conf.dist
	sed -i "s,@DATADIR@,$(installdir)$(datadir),g" $(DESTDIR)$(httpddir)/mint.conf.dist
	sed -i "s,@DESTDIR@,$(installdir),g" $(DESTDIR)$(httpddir)/mint.conf.dist
	if [ ! -e $(DESTDIR)$(httpddir)/mint.conf ]; then \
		cp -a $(DESTDIR)$(httpddir)/mint.conf.dist $(DESTDIR)$(httpddir)/mint.conf; \
	fi
	mkdir -p $(DESTDIR)$(servicedir)/authrepo
	install -m 644 authrepo.cnr $(DESTDIR)$(servicedir)/authrepo/authrepo.cnr.dist
	sed -i "s,@DESTDIR@,$(installdir),g" $(DESTDIR)$(servicedir)/authrepo/authrepo.cnr.dist
	if [ ! -e $(DESTDIR)$(servicedir)/authrepo/authrepo.cnr ]; then \
		cp -a $(DESTDIR)$(servicedir)/authrepo/authrepo.cnr.dist $(DESTDIR)$(servicedir)/authrepo/authrepo.cnr; \
	fi

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
