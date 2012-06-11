#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

.PHONY: all install $(generated_files)

PLATFORM_FILES = $(wildcard *.xml)
PLATFORMS_DIR = /usr/share/rbuilder/platforms

all: default-all

install: default-install
	install -d ${DESTDIR}$(PLATFORMS_DIR)
	install -D -m0644 $(PLATFORM_FILES) ${DESTDIR}$(PLATFORMS_DIR)

clean: default-clean


include ../../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
