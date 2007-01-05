#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#

python_files = \
	anaconda_images.py	\
	anaconda_templates.py	\
	gencslist.py		\
	group_trove.py		\
	imagegen.py		\
	__init__.py		\
	installable_iso.py	\
	jobserver.py		\
	bootable_image.py	\
	raw_fs_image.py	\
	live_iso.py		\
	netboot_image.py	\
        raw_hd_image.py         \
	stub_image.py		\
        splitdistro.py          \
        tarball.py              \
        vmware_image.py         \
	vhd.py                  \
	vpc.py

extra_dist = Makefile

dist_files = $(python_files) $(extra_dist)

all: default-all

install: install-subdirs pyfiles-install

dist: default-dist

clean: default-clean

include ../../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
