#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All rights reserved
#

SUBDIRS = static

all: default-all

python_files = __init__.py mcpweb.py

extra_files = Makefile

dist_files = $(python_files) $(extra_files)

generated_files = *.pyo *.pyc

.PHONY: clean dist install

install: all raaplugins-install

dist: default-dist

clean: default-clean

include ../../../../Make.rules
