#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#

static_files =				\
	amazon-s3-processor		\
	check-repository		\
	deleteproject			\
	ec2-terminator			\
	group-script			\
	load-offline-mirror		\
	mcp-stack			\
	migrate-all-projects		\
	mirror-inbound			\
	mirror-outbound			\
	rbuilder-database		\
	update-package-index		\
	update-package-index-external	\
	update-top-projects		\
	set-password		

override STATICDEST = /usr/share/rbuilder/scripts

all: default-all

install: static-install default-install

clean: default-clean

include ../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
