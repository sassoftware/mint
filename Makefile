#
# Copyright (c) 2005-2007 rPath, Inc.
#

# may be adjusted by recipe (via make commandline)
DESTDIR =	/
export PRODUCT =	rbuilder
export VERSION =	4.0
export SHORTVER =	$(VERSION)
export TOPDIR =		$(shell pwd)
export DISTNAME =	$(PRODUCT)-$(SHORTVER)
export DISTDIR =	$(TOPDIR)/$(DISTNAME)
export PREFIX =		/usr

# clear this (from commandline) to build rBO
PRODUCT_SUBDIRS = product

SUBDIRS = mint scripts raaplugins commands doc distro $(PRODUCT_SUBDIRS)

dist_files = Makefile Make.rules rbuilder.conf httpd.conf NEWS

generated_files = VERSION INSTALL

.PHONY: doc test $(generated_files)

## Standard rules
all: $(generated_files) default-subdirs

dist: dist-archive dist-tarball

install: all install-subdirs

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
