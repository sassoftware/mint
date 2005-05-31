#
# Copyright (c) 2005 rpath, Inc.
#
# All Rights Reserved
#
SUBDIRS = server archive

python_files =  authtest.py\
		jobtest.py\
		profiletest.py\
		projecttest.py\
		recipes.py\
		rephelp.py\
		testsuite.py\
		webtest.py

extra_dist = Makefile

dist_files = $(python_files) $(extra_dist)

all: default-all default-subdirs

clean: default-clean

dist: default-dist

install: default-install

include ../Make.rules
