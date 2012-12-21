#
# Copyright (c) rPath, Inc.
#

static_files =				\
	add-lvm-disk			\
	add-windows-build-service       \
	apply-proxy-settings		\
	check-repository		\
	create-platforms		\
	deleteproject			\
	enable-platforms	\
	fix-ec2-certificates		\
	generate-certs.sh		\
	group-script			\
	load-offline-mirror		\
	mcp-stack			\
	migrate-all-projects		\
	mirror-inbound			\
	mirror-outbound			\
	rbuilder-debug			\
	refresh-auth			\
	rmake-reset			\
	rmake-setup			\
	rss-update			\
	set-authuserpass		\
	update-bulletin			\
	update-package-index		\
	update-package-index-external	\
	set-password                    \
	$(generic_scripts)		\


generated_files = $(generic_scripts)

generic_scripts = \
	job-cleanup			\
	migrate-config			\
	pki-tool			\
	postgres-auto-update		\
	postgres-major-migrate		\
	process-system-events		\
	purge-surveys			\
	rbuilder-database		\
	repository-sync			\
	restore-preload-bundle		\
	system-resolver			\
	target-systems-import		\

cgi_files =				\
	fileupload.cgi			\
	urldownloader.cgi

override STATICDEST = /usr/share/rbuilder/scripts
override CGIDEST = /srv/www/cgi-bin

all: default-all $(generated_files)

install: static-install cgi-install default-install

clean: default-clean


$(generic_scripts): generic-script.py Makefile
	sed -e 's/some_module/$(subst -,_,$@)/g' $< >$@
	@chmod 0755 $@


include ../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
