#
# Copyright (c) 2004-2005 rPath, Inc.
#
# All Rights Reserved
#

python_files = \
	gencslist.py		\
	group_trove.py		\
	imagegen.py		\
	__init__.py		\
	installable_iso.py	\
	live_cf_image.py	\
	live_iso.py		\
	netboot_image.py	\
	stub_image.py

extra_dist = Makefile

dist_files = $(python_files) $(extra_dist)

all: default-all

install: install-subdirs pyfiles-install

dist: default-dist

clean: default-clean

include ../../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
