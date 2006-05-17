#
# Copyright (c) 2004-2005 rpath, Inc.
#
# All Rights Reserved
#

script_dist =			\
	buildtemplates		\
	create-release		\
	cvtmysql.py		\
	deleteproject.py	\
	install-jsroot		\
	job-server		\
	mirror-inbound		\
	mirror-outbound		\
	mklivecd		\
	reset			\
	update-package-index	\
	update-package-index-external

extra_dist = \
	Makefile		\
	bootable_image.conf	\
	installable_iso.conf	\
	iso_gen.conf		\
	live_iso.conf		\
	buildtemplates		\
	raw2vmdk.c		\
	job-server.init.in	\
	multi-jobserver.init.in

SUBDIRS = data DiskImageData

CFLAGS=-Wall -g -O2 -D_GNU_SOURCE -D_FILE_OFFSET_BITS=64
LDFLAGS=
CC=gcc

dist_files = $(script_dist) $(extra_dist)

all: default-all bin

bin: raw2vmdk

install: install-subdirs
	mkdir -p $(DESTDIR)/$(datadir)/rbuilder/scripts/
	for f in $(script_dist); do \
		install -m 755 $$f $(DESTDIR)/$(datadir)/rbuilder/scripts/$$f; \
	done;
	mkdir -p $(DESTDIR)/$(confdir)
	install -m 644 installable_iso.conf $(DESTDIR)/$(confdir)/installable_iso.conf.dist
	install -m 644 live_iso.conf $(DESTDIR)/$(confdir)/live_iso.conf.dist
	install -m 644 iso_gen.conf $(DESTDIR)/$(confdir)/iso_gen.conf.dist
	install -m 644 bootable_image.conf $(DESTDIR)/$(confdir)/bootable_image.conf.dist

	mkdir -p $(DESTDIR)/$(sysconfdir)/init.d/
	install -m 755 job-server.init.in $(DESTDIR)/$(sysconfdir)/init.d/rbuilder-isogen
	sed -i "s,@DESTDIR@,$(installdir),g" $(DESTDIR)/$(sysconfdir)/init.d/rbuilder-isogen
	install -m 755 multi-jobserver.init.in $(DESTDIR)/$(sysconfdir)/init.d/multi-jobserver
	sed -i "s,@DESTDIR@,$(installdir),g" $(DESTDIR)/$(sysconfdir)/init.d/multi-jobserver

	mkdir -p $(DESTDIR)/$(bindir)/
	install -m 755 raw2vmdk	$(DESTDIR)/$(bindir)/


dist: default-dist

clean: default-clean
	rm -f raw2vmdk

raw2vmdk: raw2vmdk.c
	$(CC) $(CFLAGS) -lm -o raw2vmdk raw2vmdk.c

include ../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
