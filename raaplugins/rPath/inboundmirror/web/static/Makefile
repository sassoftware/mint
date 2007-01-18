#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All rights reserved
#

SUBDIRS = images

all: default-all default-subdirs

extra_files = Makefile

dist_files = $(python_files) $(extra_files)

generated_files = *.pyo *.pyc

.PHONY: clean dist install

install: all install-subdirs

dist: default-dist dist-subdirs

clean: default-clean clean-subdirs

subdirs: default-subdirs


include ../../../../../Make.rules
