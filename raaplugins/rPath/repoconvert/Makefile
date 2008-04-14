#
# Copyright (c) 2008 rPath, Inc.
#
# All rights reserved
#

SUBDIRS = srv templates web


python_files = __init__.py

cfg_files = repoconvert.cfg


all: default-all

install: raaplugins-install default-install
	mkdir -p $(DESTDIR)/etc/raa/plugins.d
	install -m0644 $(cfg_files) $(DESTDIR)/etc/raa/plugins.d/

clean: default-clean

include ../../../Make.rules
