#
# Copyright (c) rPath, Inc.
#

static_files =				\
	add-lvm-disk			\
	add-windows-build-service	\
	apply-proxy-settings		\
	check-repository		\
	create-platforms		\
	deleteproject			\
	enable-platforms		\
	fix-ec2-certificates		\
	generate-certs.sh		\
	group-script			\
	load-offline-mirror		\
	mcp-stack			\
	migrate-all-projects		\
	post-install			\
	rbuilder-debug			\
	rmake-reset			\
	rmake-setup			\
	set-authuserpass		\
	set-password			\
	update-package-index		\
	update-package-index-external	\
	$(generic_scripts)		\


generated_files = $(generic_scripts)

generic_scripts = \
	job-cleanup			\
	migrate-config			\
	mirror-inbound			\
	mirror-outbound			\
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


override STATICDEST = /usr/share/rbuilder/scripts

all: default-all $(generated_files)

install: static-install default-install

clean: default-clean


$(generic_scripts): generic-script.py Makefile
	sed -e 's/some_module/$(subst -,_,$@)/g' $< >$@
	@chmod 0755 $@


include ../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
