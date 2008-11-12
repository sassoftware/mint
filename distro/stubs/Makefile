#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#

.PHONY: all install $(generated_files)


all: default-all $(generated_files)

install: default-install
	mkdir -p $(DESTDIR)/srv/rbuilder/config/config.d
	mkdir -p $(DESTDIR)/srv/rbuilder/config/pcreator.d
	install -D -m0660 rbuilder-generated.conf \
		$(DESTDIR)/srv/rbuilder/config/rbuilder-generated.conf
	install -D -m0640 rbuilder-custom.conf \
		$(DESTDIR)/srv/rbuilder/config/stubs/rbuilder-custom.conf
	install -D -m0644 pcreator.conf $(DESTDIR)/srv/rbuilder/config/pcreator.conf
	touch $(DESTDIR)/srv/rbuilder/config/config.d/.keep.rbuilder
	touch $(DESTDIR)/srv/rbuilder/config/pcreator.d/.keep.rbuilder

clean: default-clean


include ../../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
