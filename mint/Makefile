#
# Copyright (c) 2005 rPath, Inc.
#
# All Rights Reserved
#

SUBDIRS = web distro reports

python_files =			\
	__init__.py		\
	cache.py		\
	checkhtml.py		\
	config.py		\
	constants.py		\
	database.py		\
	dbversion.py		\
	grouptrove.py		\
	jobs.py			\
	jobdata.py		\
	jobstatus.py		\
	mailinglists.py		\
	mint_error.py		\
	mint.py			\
	mint_server.py		\
	news.py			\
	pkgindex.py		\
	projectlisting.py	\
	projects.py		\
	releases.py		\
	releasedata.py		\
	releasetypes.py		\
	requests.py		\
	searcher.py		\
	session.py		\
	sessiondb.py		\
	shimclient.py		\
	rbuilderaction.py	\
	stats.py		\
	userlevels.py		\
	userlisting.py		\
	users.py

extra_dist = Makefile constants.py.in

dist_files = $(python_files) $(extra_dist)

all: default-all default-subdirs constants.py

constants.py: constants.py.in ../Makefile
	sed s,@version@,$(VERSION),g $< > $@

install: install-subdirs pyfiles-install

dist: default-dist

clean: default-clean

include ../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
