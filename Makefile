#
# Copyright (c) 2005-2007 rPath, Inc.
#

# may be adjusted by recipe (via make commandline)
DESTDIR =	/
export PRODUCT =	rbuilder
export VERSION =	4.1
export SHORTVER =	$(VERSION)
export TOPDIR =		$(shell pwd)
export DISTNAME =	$(PRODUCT)-$(SHORTVER)
export DISTDIR =	$(TOPDIR)/$(DISTNAME)
export PREFIX =		/usr
export LIBDIR =		$(PREFIX)/lib

# from here on shouldn't need overriding
export PYTHON = $(shell [ -x /usr/bin/python2.4 ] && echo /usr/bin/python2.4 || echo /usr/lib/conary/python/bin/python2.4)
export PYVERSION = $(shell $(PYTHON) -c 'import os, sys; print sys.version[:3]')
export PYDIR = $(LIBDIR)/python$(PYVERSION)/site-packages

SUBDIRS = mint scripts raaplugins commands doc distro

dist_files = Makefile Make.rules rbuilder.conf httpd.conf NEWS

generated_files = VERSION INSTALL

.PHONY: doc mint_test $(generated_files)

## Standard rules
all: $(generated_files) default-subdirs

dist: dist-archive dist-tarball

install: install-subdirs

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
