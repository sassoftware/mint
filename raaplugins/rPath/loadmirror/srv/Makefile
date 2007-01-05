#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All rights reserved
#

all: default-all default-subdirs

python_files = __init__.py loadmirror.py

extra_files = Makefile

dist_files = $(python_files) $(extra_files)

generated_files = *.pyo *.pyc

.PHONY: clean dist install

install: all raaplugins-install

dist: default-dist

clean: default-clean

include ../../../../Make.rules
