#
# Copyright (c) 2005 rpath, Inc.
#
# All Rights Reserved
#

SUBDIRS = templates content

python_files = \
	__init__.py	\
	admin.py	\
	app.py		\
	cache.py	\
	repos.py	\
	rpchooks.py	\
	decorators.py	\
	hooks.py	\
	project.py	\
	setup.py	\
	site.py		\
	webhandler.py

extra_dist = Makefile

dist_files = $(python_files) $(extra_dist)

all: default-all default-subdirs

install: pyfiles-install install-subdirs

dist: default-dist

clean: default-clean

include ../../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
