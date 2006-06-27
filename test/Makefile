#
# Copyright (c) 2005 rpath, Inc.
#
# All Rights Reserved
#
SUBDIRS = server archive

python_files = \
               _apache.py \
               accounttest.py \
               acltest.py \
               authtest.py \
	       bootabletest.py \
               cachetest.py \
	       cmdlinetest.py \
               configtest.py \
               coverage.py \
               coveragewrapper.py \
               distrotest.py \
               emailtest.py \
               fixtures.py \
               grouptrovetest.py \
               helperfuncstest.py \
               htmltest.py \
               injectiontest.py \
               jobstest.py \
	       jobservertest.py \
               jobserverharness.py \
               joinrequesttest.py \
               labelstest.py \
               maintenancetest.py \
               mint_rephelp.py \
               mirrortest.py \
	       mirrorprimetest.py \
               producttest.py \
               projecttest.py \
               recipes.py \
               repostest.py \
               reportstest.py \
               rmakebuildtest.py \
               rmakestatustest.py \
               schematest.py \
               searchtest.py \
               sessionstest.py \
               spidertest.py \
               testsuite.py \
               usertest.py \
               xmltest.py \
               webtest.py \
               webmemberstest.py \
	       websetuptest.py \
	       webrepostest.py \
	       webprojecttest.py

extra_dist = Makefile

dist_files = $(python_files) $(extra_dist)

all: default-all default-subdirs

clean: default-clean

dist: default-dist

install: default-install

include ../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
