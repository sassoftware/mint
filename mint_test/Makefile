#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#
SUBDIRS = server mint_archive

python_files = \
               _apache.py \
               accounttest.py \
               authtest.py \
               cachetest.py \
	       cmdlinetest.py \
               configtest.py \
               coverage.py \
               coveragewrapper.py \
	       ec2test.py \
               fixtures.py \
               grouptrovetest.py \
               helperfuncstest.py \
               htmltest.py \
               injectiontest.py \
               jobserverharness.py \
               joinrequesttest.py \
               labelstest.py \
               marketingtest.py	\
               mint_rephelp.py \
               mirrortest.py \
               buildtest.py \
               projecttest.py \
	       productversiontest.py \
               pubreleasetest.py \
               recipes.py \
               repostest.py \
               reportstest.py \
               schematest.py \
               searchtest.py \
               sessionstest.py \
               spidertest.py \
               testsuite.py \
	       updateservicetest.py \
               usertest.py \
               xmltest.py \
               webtest.py \
	       webhandlertest.py \
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
