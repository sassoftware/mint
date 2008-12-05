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
	migrate-config			\
	mirror-inbound			\
	mirror-outbound			\
	rbuilder-database		\
	rmake-setup			\
	update-package-index		\
	update-package-index-external	\
	update-top-projects		\
	set-password

generated_files =	\
	rbuilder_database.py

cgi_files =				\
	fileupload.cgi

override STATICDEST = /usr/share/rbuilder/scripts
override CGIDEST = /srv/www/cgi-bin

all: default-all

install: static-install cgi-install default-install

clean: default-clean

include ../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
