#
# Copyright (c) 2005 rpath, Inc.
#
# All Rights Reserved
#

SUBDIRS = templates content

python_files = \
	__init__.py		\
        app.py			\
	cookie_http.py	\
        hooks.py

extra_dist = Makefile

dist_files = $(python_files) $(extra_dist)

all: default-all default-subdirs

install: pyfiles-install install-subdirs

dist: default-dist

clean: default-clean

include ../../Make.rules
