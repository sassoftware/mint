#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#

SUBDIRS = cmdline reports templates web

python_files =			\
	__init__.py		\
	accesscontrol.py	\
	backup.py		\
	builds.py		\
	buildtemplates.py	\
	buildtypes.py		\
	buildxml.py             \
	charts.py		\
	checkhtml.py		\
	client.py		\
	communityids.py		\
	communitytypes.py	\
	config.py		\
	cooktypes.py		\
	constants.py		\
	copyutils.py		\
	data.py			\
	database.py		\
	dbversion.py		\
	ec2.py			\
	flavors.py		\
	grouptrove.py		\
	helperfuncs.py		\
	jobs.py			\
	jobstatus.py		\
	loadmirror.py		\
	mailinglists.py		\
	maintenance.py		\
	mint_error.py		\
	mint_update.py		\
	mirror.py		\
	news.py			\
	pkgindex.py		\
	pkgindexer.py		\
	profile.py		\
	projects.py		\
	pubreleases.py		\
	rapapasswords.py	\
	rbuilderaction.py	\
	requests.py		\
	rmakebuild.py		\
	rmakeconstants.py	\
	schema.py		\
	scriptlibrary.py	\
	searcher.py		\
	selections.py		\
	server.py		\
	session.py		\
	sessiondb.py		\
	shimclient.py		\
	spotlight.py		\
	stats.py		\
	urltypes.py		\
	useit.py		\
	userlevels.py		\
	userlisting.py		\
	users.py		\
	usertemplates.py

extra_dist = rmakeconstants.py.in.py

override PYDEST = mint

generated_files = constants.py rmakeconstants.py


.PHONY: clean install $(generated_files)

all: $(generated_files) default-all

install: all pyfiles-install default-install

clean: default-clean


constants.py: constants.py.in
	sed -e s,@version@,$(VERSION),g $< > $@

rmakeconstants.py: rmakeconstants.py.in.py
	python rmakeconstants.py.in.py


include ../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
