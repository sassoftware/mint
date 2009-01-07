#
# Copyright (c) 2008-2009 rPath, Inc.
#
# All rights reserved
#

SUBDIRS = srv web help

python_files = __init__.py

kid_files = index.kid \
			nodes.kid

cfg_files = rmakemanagement.cfg

all: kid-build default-all

install: raaplugins-install default-install
	mkdir -p $(DESTDIR)/etc/raa/plugins.d
	install -m0644 $(cfg_files) $(DESTDIR)/etc/raa/plugins.d/

clean: kid-clean default-clean

include ../../../Make.rules
