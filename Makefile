#
# Copyright (c) 2010 rPath, Inc.
#
# All rights reserved.
#

# may be adjusted by recipe (via make commandline)
export DESTDIR =	/
export PRODUCT =	rbuilder
export VERSION =	5.7.0
export SHORTVER =	$(VERSION)
export TOPDIR =		$(shell pwd)
export DISTNAME =	$(PRODUCT)-$(SHORTVER)
export DISTDIR =	$(TOPDIR)/$(DISTNAME)
export PREFIX =		/usr
export lib =		$(shell uname -m | sed -r '/x86_64|ppc64|s390x|sparc64/{s/.*/lib64/;q};s/.*/lib/')
export LIBDIR =		$(PREFIX)/$(lib)
export PYVER =		"`python -c 'import sys; print sys.version[0:3]'`"
export POSTGRES_VERSION = 9.0

# from here on shouldn't need overriding
export PYTHON = /usr/bin/python$(PYVER)
export PYDIR = $(LIBDIR)/python$(PYVER)/site-packages

SUBDIRS = mint scripts raaplugins rmake_plugins doc distro

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
