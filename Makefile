#
# Copyright (c) SAS Institute Inc.
#

# may be adjusted by recipe (via make commandline)
export DESTDIR =	/
export PRODUCT =	rbuilder
export VERSION =	8
export SHORTVER =	$(VERSION)
export TOPDIR =		$(shell pwd)
export DISTNAME =	$(PRODUCT)-$(SHORTVER)
export DISTDIR =	$(TOPDIR)/$(DISTNAME)
export PREFIX =		/usr
export lib =		$(shell uname -m | sed -r '/x86_64|ppc64|s390x|sparc64/{s/.*/lib64/;q};s/.*/lib/')
export LIBDIR =		$(PREFIX)/$(lib)
export POSTGRES_VERSION = 9.0

# from here on shouldn't need overriding
export PYTHON = /usr/bin/python
export PYVER = $(shell $(PYTHON) -c 'import sys; print sys.version[0:3]')
export PYDIR = $(LIBDIR)/python$(PYVER)/site-packages

SUBDIRS = mint scripts rmake_plugins distro twisted ha puppet

dist_files = Makefile Make.rules rbuilder.conf httpd.conf NEWS

.PHONY: mint_test $(generated_files)

## Standard rules
all: $(generated_files) default-subdirs

dist: dist-archive dist-tarball

install: install-subdirs

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


include Make.rules

# vim: set sts=8 sw=8 noexpandtab :
