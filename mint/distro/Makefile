#
# Copyright (c) 2004-2005 rPath, Inc.
#
# All Rights Reserved
#

python_files = \
	anaconda_images.py	\
	flavors.py		\
	gencslist.py		\
	group_trove.py		\
	imagegen.py		\
	__init__.py		\
	installable_iso.py	\
	jobserver.py		\
	jsversion.py            \
	bootable_image.py	\
	raw_fs_image.py	\
	live_iso.py		\
	netboot_image.py	\
        raw_hd_image.py         \
	stub_image.py		\
        splitdistro.py          \
        tarball.py              \
        vmware_image.py         \
        conaryinstall.py

extra_dist = Makefile

dist_files = $(python_files) $(extra_dist)

all: default-all

install: install-subdirs pyfiles-install

dist: default-dist

clean: default-clean

include ../../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
