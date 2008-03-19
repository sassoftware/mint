#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All rights reserved
#

all: default-all default-subdirs

SUBDIRS = 

python_files = repoconvert.py \
	__init__.py

extra_files = Makefile

dist_files = $(python_files) $(extra_files)

generated_files = *.pyo *.pyc

.PHONY: clean dist install subdirs

subdirs: default-subdirs

install: all install-subdirs pyfiles-install
	$(PYTHON) -c "import compileall; compileall.compile_dir('$(DESTDIR)$(pluginsdir)', ddir='$(pluginsdir)', quiet=1)"
	$(PYTHON) -OO -c "import compileall; compileall.compile_dir('$(DESTDIR)$(pluginsdir)', ddir='$(pluginsdir)', quiet=1)"

dist: default-dist

clean: clean-subdirs default-clean

include ../../Make.rules
