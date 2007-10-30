#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#

wrapped_scripts =				\
	amazon-s3-processor		\
	check-repository		\
	deleteproject			\
	ec2-terminator			\
	load-offline-mirror		\
	mcp-stack			\
	migrate-all-projects		\
	migrate-config			\
	mirror-inbound			\
	mirror-outbound			\
	rbuilder-backup			\
	rbuilder-database		\
	update-package-index		\
	update-package-index-external	\
	update-top-projects		\
	set-password		

wrapper_script = wrapper.sh

generated_files = $(wrapper_script)

extra_dist = wrapper.sh.in

override WRAPPEDSCRIPTSDEST = /usr/libexec/rbuilder
override WRAPPERDEST = /usr/share/rbuilder/scripts

all: default-all $(generated_files)

install: wrapper-install default-install

clean: default-clean

wrapper.sh: wrapper.sh.in
	sed -e's,@SITEPKG@,$(PYDIR),g' -e's,@LIBEXECDIR@,$(LIBEXECDIR),g' wrapper.sh.in > wrapper.sh

include ../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
