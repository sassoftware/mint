#
# Copyright (c) 2004-2005 rpath, Inc.
#
# All Rights Reserved
#

script_dist =			\
	buildinstall		\
	buildtemplates		\
	cvtmysql.py		\
	job-server		\
	MakeDiskImage.py	\
	mklivecd		\
	reset			\
	splitdistro		\
	update-package-index

extra_dist = \
	Makefile		\
	installable_iso.conf	\
	iso_gen.conf		\
	live_iso.conf		\
	buildiso		\
	buildtemplates		\
	job-server.init.in

SUBDIRS = data

dist_files = $(script_dist) $(extra_dist)

all: default-all

install: install-subdirs
	mkdir -p $(DESTDIR)/$(datadir)/mint/scripts/
	for f in $(script_dist); do \
		install -m 755 $$f $(DESTDIR)/$(datadir)/mint/scripts/$$f; \
	done;
	mkdir -p $(DESTDIR)/$(confdir)
	install -m 644 installable_iso.conf $(DESTDIR)/$(confdir)/installable_iso.conf.dist
	install -m 644 live_iso.conf $(DESTDIR)/$(confdir)/live_iso.conf.dist
	install -m 644 iso_gen.conf $(DESTDIR)/$(confdir)/iso_gen.conf.dist

	mkdir -p $(DESTDIR)/$(sysconfdir)/init.d/
	install -m 755 job-server.init.in $(DESTDIR)/$(sysconfdir)/init.d/rbuilder-isogen
	sed -i "s,@DESTDIR@,$(installdir),g" $(DESTDIR)/$(sysconfdir)/init.d/rbuilder-isogen


dist: default-dist

clean: default-clean

include ../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
