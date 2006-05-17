#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All rights reserved
#

all: subdirs

SUBDIRS=rbalog

extra_files = \
	Makefile		\

dist_files = $(extra_files)

.PHONY: clean dist install subdirs

dist: default-dist

clean: default-clean

subdirs: default-subdirs

install: install-subdirs

include ../Make.rules
