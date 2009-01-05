#
# Copyright (c) 2008 rPath, Inc.
#
# All Rights Reserved
#
# NB: This Makefile does not regenerate artwork as that is rarely
# needed and it would bloat build dependencies greatly.

.PHONY: all install clean

legacy_files = $(wildcard *.png)


all: default-all

install: default-install
	mkdir -p $(DESTDIR)/usr/share/anaconda/pixmaps
	install -m0644 $(legacy_files) $(DESTDIR)/usr/share/anaconda/pixmaps/

clean: default-clean


include ../../../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
