#
# Copyright (c) 2009 rPath, Inc.
#
# All rights reserved.
#

SUBDIRS = rbuilder templates

python_files = $(wildcard *.py)

all: default-all comments

install: pyfiles-install default-install

comments:
	PYTHONPATH=../.. python manage_local.py gencomments

clean: default-clean


include ../../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
