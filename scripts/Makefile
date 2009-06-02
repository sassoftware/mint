#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#

static_files =				\
	amazon-s3-processor		\
	auth-generate			\
	check-repository		\
	deleteproject			\
	ec2-terminator			\
	fix-ec2-certificates		\
	generate-certs.sh		\
	group-script			\
	init-extproducts	        \
	load-offline-mirror		\
	mcp-stack			\
	migrate-all-projects		\
	migrate-config			\
	mirror-inbound			\
	mirror-outbound			\
	rbuilder-database		\
	refresh-auth			\
	rmake-setup			\
	rss-update			\
	update-bulletin			\
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

all: default-all httpdgraceful

install: static-install cgi-install default-install httpdgraceful-install

clean: default-clean httpdgraceful-clean

httpdgraceful:
	gcc httpd-graceful.c -o httpd-graceful

httpdgraceful-install:
	install -D -m4755 httpd-graceful $(DESTDIR)/usr/libexec/rbuilder/httpd-graceful

httpdgraceful-clean:
	rm -f httpd-graceful

include ../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
