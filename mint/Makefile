#
# Copyright (c) 2005 rPath, Inc.
#
# All Rights Reserved
#

SUBDIRS = web distro reports templates cmdline

python_files =			\
	__init__.py		\
	accesscontrol.py	\
	spotlight.py		\
	checkhtml.py		\
	client.py		\
	config.py		\
	constants.py		\
	cooktypes.py		\
	data.py			\
	database.py		\
	dbversion.py		\
	flavors.py		\
	grouptrove.py		\
	helperfuncs.py		\
	jobs.py			\
	jobstatus.py		\
	jsversion.py		\
	maintenance.py		\
	mailinglists.py		\
	mint_error.py		\
	mirror.py		\
	mirrorprime.py		\
	news.py			\
	pkgindex.py		\
	profile.py		\
	projectlisting.py	\
	builds.py		\
	projects.py		\
	buildtypes.py		\
	buildtemplates.py	\
	pubreleases.py		\
	requests.py		\
	rmakebuild.py		\
	rmakeconstants.py	\
	scriptlibrary.py	\
	searcher.py		\
	selections.py		\
	server.py		\
	session.py		\
	sessiondb.py		\
	shimclient.py		\
	rbuilderaction.py	\
	stats.py		\
	userlevels.py		\
	userlisting.py		\
	users.py                \
    usertemplates.py	\
	useit.py

extra_dist = Makefile constants.py.in rmakeconstants.py.in

dist_files = $(python_files) $(extra_dist)

all: default-all default-subdirs constants.py rmakeconstants.py

generated_files = *.pyo *.pyc

.PHONY: clean dist install subdirs rmakeconstants.py

subdir: default-subdirs

constants.py: constants.py.in ../Makefile
	sed s,@version@,$(VERSION),g $< > $@

rmakeconstants.py: rmakeconstants.py.in
	rm -f rmakeconstants.py
	cp rmakeconstants.py.in rmakeconstants.py
	python -c "from rmake.build.buildjob import jobStates; print 'buildjob = Constants(' + ',\n'.join(str(jobStates).split(',')) + ')'; print ''" >> rmakeconstants.py
	python -c "from rmake.build.buildtrove import troveStates; print 'buildtrove = Constants(' + ',\n'.join(str(troveStates).split(',')) + ')'" >> rmakeconstants.py

install: all install-subdirs pyfiles-install
	python -c "import compileall; compileall.compile_dir('$(DESTDIR)$(mintdir)', ddir='$(mintdir)', quiet=1)"
	python -OO -c "import compileall; compileall.compile_dir('$(DESTDIR)$(mintdir)', ddir='$(mintdir)', quiet=1)"

dist: default-dist

clean: default-clean

include ../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
