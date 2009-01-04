#
# Copyright (c) 2008 rPath, Inc.
#
# All Rights Reserved
#
# NB: This Makefile does not regenerate artwork as that is rarely
# needed and it would bloat build dependencies greatly.

.PHONY: all install clean


all: default-all

install: default-install
	install -D -m0644 bootloader_splash.png $(DESTDIR)/boot/extlinux/rbuilder_background.png

clean: default-clean


include ../../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
