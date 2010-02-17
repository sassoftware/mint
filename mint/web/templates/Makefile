#
# Copyright (c) 2005-2008 rPath, Inc.
#
# All Rights Reserved
#

SUBDIRS = repos admin docs

kid_files = $(wildcard *.kid)

python_files = __init__.py

all: kid-build default-all

install: kid-install pyfiles-install default-install

clean: kid-clean default-clean


include ../../../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
