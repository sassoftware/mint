#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All rights reserved
#

all: default-all default-subdirs

SUBDIRS = srv \
	templates \
	web

python_files = __init__.py

cfg_files = repoconvert.cfg

extra_files = Makefile $(cfg_files)

dist_files = $(python_files) $(extra_files)

generated_files = *.pyo *.pyc

.PHONY: clean dist install subdirs

subdirs: default-subdirs

install: all install-subdirs pyfiles-install cfg-install
	$(PYTHON) -c "import compileall; compileall.compile_dir('$(DESTDIR)$(pluginsdir)', ddir='$(pluginsdir)', quiet=1)"
	$(PYTHON) -OO -c "import compileall; compileall.compile_dir('$(DESTDIR)$(pluginsdir)', ddir='$(pluginsdir)', quiet=1)"

cfg-install:
	mkdir -p $(DESTDIR)/etc/raa/plugins.d
	install -m0644 $(cfg_files) $(DESTDIR)/etc/raa/plugins.d/

dist: default-dist

clean: clean-subdirs default-clean

include ../Make.rules
