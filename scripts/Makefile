#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

static_files =				\
	add-lvm-disk			\
	add-windows-build-service       \
	amazon-s3-processor		\
	apply-proxy-settings		\
	auth-generate			\
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
	refresh-auth			\
	restore-preload-bundle		\
	rmake-reset			\
	rmake-setup			\
	rss-update			\
	set-authuserpass		\
	update-bulletin			\
	update-package-index		\
	update-package-index-external	\
	validate-proxy-settings		\
	set-password                    \
	repository-log-scrape		\
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
