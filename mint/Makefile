#
# Copyright (c) 2005 rpath, Inc.
#
# All Rights Reserved
#

SUBDIRS = web distro

python_files =			\
	cache.py		\
	config.py		\
	database.py		\
	__init__.py		\
	jobs.py			\
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
	releasetypes.py		\
	searcher.py		\
	shimclient.py		\
	statsaction.py		\
	stats.py		\
	userlevels.py		\
	userlisting.py		\
	users.py		\

extra_dist = Makefile

dist_files = $(python_files) $(extra_dist)

all: default-all default-subdirs

install: install-subdirs pyfiles-install

dist: default-dist

clean: default-clean

include ../Make.rules
