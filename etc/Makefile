#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#

extra_dist =			\
	Makefile		\

SUBDIRS = httpd jobserver

dist_files = $(extra_dist)

all: default-all

install: install-subdirs

dist: default-dist dist-subdirs

clean: default-clean clean-subdirs

include ../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
