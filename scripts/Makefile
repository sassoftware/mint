#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#

static_files =				\
	amazon-s3-processor		\
	apply-proxy-settings		\
	auth-generate			\
	check-repository		\
	deleteproject			\
	ec2-terminator			\
	enable-platforms	\
	fix-ec2-certificates		\
	generate-certs.sh		\
	group-script			\
	init-extproducts	        \
	job-cleanup			\
	load-offline-mirror		\
	mcp-stack			\
	migrate-all-projects		\
	migrate-config			\
	mirror-inbound			\
	mirror-outbound			\
	rbuilder-database		\
	refresh-auth			\
	rmake-reset			\
	rmake-setup			\
	rss-update			\
	update-bulletin			\
	update-package-index		\
	update-package-index-external	\
	update-top-projects		\
	validate-proxy-settings		\
	set-password                    \
	repository-log-scrape

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
