#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All rights reserved
#

all: subdirs

SUBDIRS=rbalog loadmirror

python_files = __init__.py

extra_files = Makefile

dist_files = $(extra_files) $(python_files)

.PHONY: clean dist install subdirs

dist: default-dist

clean: default-clean

subdirs: default-subdirs

install: install-subdirs

include ../../Make.rules
