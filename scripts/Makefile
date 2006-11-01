#
# Copyright (c) 2004-2005 rpath, Inc.
#
# All Rights Reserved
#

script_dist =				\
	deleteproject			\
	install-jsroot			\
	job-server			\
	load-offline-mirror		\
	migrate-all-projects		\
	migrate-config			\
	mirror-inbound			\
	mirror-outbound			\
	mirror-prime-server		\
	update-package-index		\
	update-package-index-external	\
	set-password

extra_dist = \
	Makefile		\
	raw2vmdk.c		\
	rootstat_wrapper.c	\
	job-server.init.in	\
	multi-jobserver.init.in	\
        cleanup-bindmounts.init.in

SUBDIRS = data DiskImageData mailman

CFLAGS=-Wall -s -O2 -D_GNU_SOURCE -D_FILE_OFFSET_BITS=64
LDFLAGS=
CC=gcc

dist_files = $(script_dist) $(extra_dist)

all: default-all bin

bin: raw2vmdk rootstat_wrapper.so

install: install-subdirs
	mkdir -p $(DESTDIR)/$(datadir)/rbuilder/scripts/
	for f in $(script_dist); do \
		install -m 755 $$f $(DESTDIR)/$(datadir)/rbuilder/scripts/$$f; \
	done;

	mkdir -p $(DESTDIR)/$(sysconfdir)/init.d/
	install -m 755 job-server.init.in $(DESTDIR)/$(sysconfdir)/init.d/rbuilder-isogen
	sed -i "s,@DESTDIR@,$(installdir),g" $(DESTDIR)/$(sysconfdir)/init.d/rbuilder-isogen
	install -m 755 multi-jobserver.init.in $(DESTDIR)/$(sysconfdir)/init.d/multi-jobserver
	sed -i "s,@DESTDIR@,$(installdir),g" $(DESTDIR)/$(sysconfdir)/init.d/multi-jobserver
	install -m 755 cleanup-bindmounts.init.in $(DESTDIR)/$(sysconfdir)/init.d/cleanup-bindmounts
	sed -i "s,@DESTDIR@,$(installdir),g" $(DESTDIR)/$(sysconfdir)/init.d/cleanup-bindmounts

	mkdir -p $(DESTDIR)/$(bindir)/
	install -m 755 raw2vmdk	$(DESTDIR)/$(bindir)/
	mkdir -p $(DESTDIR)/$(libdir)/rbuilder/
	install -m 755 rootstat_wrapper.so $(DESTDIR)/$(libdir)/rbuilder/

dist: default-dist

clean: default-clean
	rm -f raw2vmdk

raw2vmdk: raw2vmdk.c
	$(CC) $(CFLAGS) -lm -o raw2vmdk raw2vmdk.c

rootstat_wrapper.o: rootstat_wrapper.c
	$(CC) -Wall -O2 -s -fPIC -rdynamic -c rootstat_wrapper.c

rootstat_wrapper.so: rootstat_wrapper.o
	$(CC) -s -shared -rdynamic -o rootstat_wrapper.so rootstat_wrapper.o -lc -ldl

include ../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
