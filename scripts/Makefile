#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#

script_dist =				\
	amazon-s3-processor		\
	check-repository		\
	deleteproject			\
	load-offline-mirror		\
	migrate-all-projects		\
	migrate-config			\
	mirror-inbound			\
	mirror-outbound			\
	update-package-index		\
	update-package-index-external	\
	update-top-projects		\
	set-password		

extra_dist = \
	Makefile		\
        backup

SUBDIRS = mailman

dist_files = $(script_dist) $(extra_dist)

all: default-all

install: install-subdirs
	mkdir -p $(DESTDIR)/$(datadir)/rbuilder/scripts/
	for f in $(script_dist); do \
		install -m 755 $$f $(DESTDIR)/$(datadir)/rbuilder/scripts/$$f; \
	done;

	mkdir -p $(DESTDIR)/etc/raa/backup.d
	install -m 755 backup $(DESTDIR)/etc/raa/backup.d/rbuilder-backup

	mkdir -p $(DESTDIR)/$(libdir)/rbuilder/

dist: default-dist

clean: default-clean

include ../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
