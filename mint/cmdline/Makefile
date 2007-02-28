#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#

python_files =		\
	__init__.py	\
	commands.py	\
	builds.py	\
	refs.py		\
	users.py

extra_dist = Makefile

dist_files = $(python_files) $(extra_dist)

all: default-all

install: install-subdirs pyfiles-install

dist: default-dist

clean: default-clean

include ../../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
