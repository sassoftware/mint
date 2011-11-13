#
# Copyright (c) 2011 rPath, Inc.
#

.PHONY: all install $(generated_files)

override STATICDEST = /usr/share/rbuilder/project-templates
static_files = $(wildcard *.xml)

all: default-all

install: default-install static-install

clean: default-clean


include ../../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
