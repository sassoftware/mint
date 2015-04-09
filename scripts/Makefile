#
# Copyright (c) SAS Institute Inc.
#

static_files =				\
	add-lvm-disk			\
	add-rmake3-node			\
	dump-rbuilder-databases		\
	deleteproject			\
	generate-certs.sh		\
	group-script			\
	mcp-stack			\
	migrate-all-projects		\
	post-install			\
	preconfigure			\
	rbuilder-debug			\
	rmake-reset			\
	rmake-setup.pp			\
	set-authuserpass		\
	set-password			\
	update-package-index		\
	update-package-index-external	\
	$(generic_scripts)		\


generated_files = $(generic_scripts)

generic_scripts = \
	job-cleanup			\
	mint-admin			\
	mirror-inbound			\
	mirror-outbound			\
	pki-tool			\
	postgres-auto-update		\
	postgres-major-migrate		\
	process-system-events		\
	rbuilder-database		\
	repository-sync			\


override STATICDEST = /usr/share/rbuilder/scripts

all: default-all $(generated_files)

install: static-install default-install

clean: default-clean


$(generic_scripts): generic-script.py Makefile
	sed -e 's/some_module/$(subst -,_,$@)/g' $< >$@
	@chmod 0755 $@


include ../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
