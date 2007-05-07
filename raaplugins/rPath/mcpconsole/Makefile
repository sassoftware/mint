#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All rights reserved
#

all: default-all default-subdirs

SUBDIRS = web templates

python_files = __init__.py

kid_files =

extra_files = Makefile

dist_files = $(python_files) $(extra_files) $(kid_files)

generated_files = *.pyo *.pyc

.PHONY: clean dist install subdirs

subdirs: default-subdirs

install: all install-subdirs raaplugins-install
	$(PYTHON) -c "import compileall; compileall.compile_dir('$(DESTDIR)$(raapluginsdir)', ddir='$(raapluginsdir)', quiet=1)"
	$(PYTHON) -OO -c "import compileall; compileall.compile_dir('$(DESTDIR)$(raapluginsdir)', ddir='$(raapluginsdir)', quiet=1)"

dist: default-dist dist-subdirs

clean: clean-subdirs default-clean

include ../../../Make.rules
