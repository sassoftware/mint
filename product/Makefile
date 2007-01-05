#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#

SUBDIRS = content templates datatemplates

dist_files = rbuilder.conf httpd.conf

all: default-subdirs

install: install-subdirs

subdirs: default-subdirs

dist: defaultdist dist-subdirs

defaultdist: $(dist_files)
	mkdir -p $(DISTDIR)
	for f in $(dist_files); do \
		cp -a $$f $(DISTDIR); \
	done

clean: default-clean clean-subdirs

include ../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
