#
# Copyright (c) 2006 rPath, Inc.
#
# All Rights Reserved
#

conf_dist = \
	bootable_image.conf	\
	installable_iso.conf	\
	iso_gen.conf		\
	live_iso.conf

extra_dist = Makefile

SUBDIRS =

dist_files = $(conf_dist) $(extra_dist)

all: default-all bin

install: install-subdirs
	mkdir -p $(DESTDIR)/$(confdir)
	install -m 644 installable_iso.conf $(DESTDIR)/$(confdir)/installable_iso.conf.dist
	install -m 644 live_iso.conf $(DESTDIR)/$(confdir)/live_iso.conf.dist
	install -m 644 iso_gen.conf $(DESTDIR)/$(confdir)/iso_gen.conf.dist
	install -m 644 bootable_image.conf $(DESTDIR)/$(confdir)/bootable_image.conf.dist

dist: default-dist

clean: default-clean

include ../../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
