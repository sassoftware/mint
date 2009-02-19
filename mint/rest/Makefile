#
# Copyright (c) 2005-2008 rPath, Inc.
#
# All Rights Reserved
#

SUBDIRS = api db middleware modellib 

python_files = $(wildcard *.py)


.PHONY: clean install $(generated_files)

all: $(generated_files) default-all

install: pyfiles-install default-install

clean: default-clean

include ../../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
