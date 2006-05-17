#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All rights reserved
#

all: default-all

SUBDIRS = 

python_files = rbalog.py __init__.py

extra_files = Makefile

dist_files = $(python_files) $(extra_files)

generated_files = *.pyo *.pyc

.PHONY: clean dist install

install: all raaplugins-install
	$(PYTHON) -c "import compileall; compileall.compile_dir('$(DESTDIR)$(raapluginsdir)', ddir='$(raapluginsdir)', quiet=1)"
	$(PYTHON) -OO -c "import compileall; compileall.compile_dir('$(DESTDIR)$(raapluginsdir)', ddir='$(raapluginsdir)', quiet=1)"

dist: default-dist

clean: default-clean

include ../../../Make.rules
