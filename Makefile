#
# Copyright (c) 2005-2007 rPath, Inc.
#

# may be adjusted by recipe (via make commandline)
export DESTDIR =	/
export PRODUCT =	rbuilder
export VERSION =	4.0		# full version, maybe w/ changeset id
export SHORTVER =	$(VERSION)	# just the meatstring (4.0.0)
export TOPDIR =		$(shell pwd)
export DISTNAME =	$(PRODUCT)-$(SHORTVER)
export DISTDIR =	$(TOPDIR)/$(DISTNAME)
export PREFIX =		/usr

# generally not touched
export sysconfdir =	/etc
export servicedir =	/srv
export confdir =	$(servicedir)/rbuilder/
export datadir =	$(PREFIX)/share
export mandir =		$(datadir)/man
export contentdir =	$(datadir)/conary/web-common/apps/mint/
export libdir =		$(PREFIX)/lib
export bindir =		$(PREFIX)/bin
export localedir =	$(datadir)/locale
export mintdir =	$(libdir)/python$(PYVERSION)/site-packages/
export httpddir =	$(sysconfdir)/httpd/conf.d/
export maillistdir =	/var/mailman
export raapluginsdir =	$(libdir)/raa/rPath/

SUBDIRS = mint product test scripts raaplugins commands etc doc locales

dist_files = Makefile Make.rules rbuilder.conf httpd.conf NEWS

generated_files = VERSION INSTALL

.PHONY: doc test $(generated_files)

## Standard rules
all: $(generated_files) default-subdirs

dist: dist-archive dist-tarball

install: all install-subdirs
	mkdir -p $(DESTDIR)$(datadir)/rbuilder/
	mkdir -p $(DESTDIR)$(confdir)
	mkdir -p $(DESTDIR)$(httpddir)
	install httpd.conf $(DESTDIR)$(httpddir)/rbuilder.conf.dist
	sed -i "s,@DATADIR@,$(DESTDIR)$(datadir),g" $(DESTDIR)$(httpddir)/rbuilder.conf.dist
	sed -i "s,@DESTDIR@,$(DESTDIR),g" $(DESTDIR)$(httpddir)/rbuilder.conf.dist
	python -c "from mint import database; print database.DatabaseTable.schemaVersion" > $(DESTDIR)$(datadir)/rbuilder/schema

doc:
	PYTHONPATH=.:../conary/: epydoc -o mintdoc mint

clean: clean-subdirs default-clean


## Tarball generation

dist-archive:
	@if [ ! -d .hg ]; then \
		echo "make dist" must be run from a mercurial checkout.; \
		exit 1; \
	fi
	rm -rf $(DISTDIR)
	hg archive $(DISTDIR)
	rm $(DISTDIR)/.hgtags

dist-tarball:
	tar -cjf $(DISTNAME).tar.bz2 $(DISTNAME)/
	rm -rf $(DISTDIR)


## Generated files
INSTALL: INSTALL.in
	sed -e s,@version@,$(VERSION),g $< > $@

VERSION:
	echo "This is rBuilder $(VERSION)" > VERSION


## Dist-specific rules
strip-raa:
	rm -rf $(DISTDIR)/raaplugins/*
	echo "all: " > $(DISTDIR)/raaplugins/Makefile
	echo "install: " >> $(DISTDIR)/raaplugins/Makefile

dummy:
	echo VERSION: $(VERSION)
	echo DISTDIR: $(DISTDIR)

include Make.rules

# vim: set sts=8 sw=8 noexpandtab :
