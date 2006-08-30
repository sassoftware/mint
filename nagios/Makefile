#
# Copyright (c) 2005 rPath, Inc.
#
# All Rights Reserved
#

SUBDIRS = 

python_files =			\
		checkjs.py		\
		checkjsrb.py	\
		check_js		\
		check_js_rb

extra_dist = Makefile

dist_files = $(python_files) $(extra_dist)

all: default-all

dist: default-dist dist-subdirs

clean: default-clean clean-subdirs

include ../Make.rules

# vim: set sts=8 sw=8 noexpandtab :
