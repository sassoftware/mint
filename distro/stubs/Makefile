#
# Copyright (c) SAS Institute Inc.
#

.PHONY: all install $(generated_files)


all: default-all $(generated_files)

install: default-install
	# Empty target directories for custom configuration.
	mkdir -p $(DESTDIR)/etc/rmake/node.d
	mkdir -p $(DESTDIR)/srv/rbuilder/config/config.d
	# Install include-* stubs and defaults (Transient)
	install -D -m0644 noderc $(DESTDIR)/etc/rmake/noderc
	# Install stubs to be overwritten by setup and/or rAPA.
	# (InitialContents, possibly group-writable w/ Ownership)
	install -D -m0664 noderc.rapa \
		$(DESTDIR)/etc/rmake/node.d/25_rbuilder-rapa.conf
	# "dot-keep" files to preserve the empty config directories.
	# This is marginally simpler than policy as long as the
	# dirs are root-owned, and keeps everything in one place.
	touch $(DESTDIR)/srv/rbuilder/config/config.d/.keep.rbuilder

clean: default-clean


include ../../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
