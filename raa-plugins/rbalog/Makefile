#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All rights reserved
#

all: default-all default-subdirs

SUBDIRS = web

python_files = __init__.py

kid_files = log.kid

extra_files = Makefile

dist_files = $(python_files) $(extra_files) $(kid_files)

generated_files = *.pyo *.pyc

.PHONY: clean dist install subdirs

subdirs: default-subdirs

install: all install-subdirs raaplugins-install kidfiles-install
	$(PYTHON) -c "import compileall; compileall.compile_dir('$(DESTDIR)$(raapluginsdir)', ddir='$(raapluginsdir)', quiet=1)"
	$(PYTHON) -OO -c "import compileall; compileall.compile_dir('$(DESTDIR)$(raapluginsdir)', ddir='$(raapluginsdir)', quiet=1)"

kidfiles-install:
	kidc --strip-dest-dir $$(pwd) $(kid_files)
	mkdir -p $(DESTDIR)$(raapluginsdir)`echo $(DIR) | sed "s|/raa-plugins||"`
	for f in $(kid_files) *.pyc; do \
		cp -a $$f $(DESTDIR)$(raapluginsdir)`echo $(DIR) | sed "s|/raa-plugins||"`/$$f; \
	done

dist: default-dist

clean: clean-subdirs default-clean

include ../../Make.rules
