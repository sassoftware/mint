#
# Copyright (c) 2005 rpath, Inc.
#
# All Rights Reserved
#
SUBDIRS = server archive

python_files = \
               accounttest.py \
               acltest.py \
               authtest.py \
               cachetest.py \
               configtest.py \
               coverage.py \
               coveragewrapper.py \
               distrotest.py \
               grouptrovetest.py \
               helperfuncstest.py \
               htmltest.py \
               injectiontest.py \
               jobstest.py \
	       jobservertest.py \
               jobserverharness.py \
               joinrequesttest.py \
               labelstest.py \
               mint_rephelp.py \
               mirrortest.py \
               projecttest.py \
               recipes.py \
               releasetest.py \
               repostest.py \
               reportstest.py \
               schematest.py \
               searchtest.py \
               sessionstest.py \
               testsuite.py \
               xmltest.py \
               webtest.py \
               webmemberstest.py \
	       websetuptest.py \
	       webrepostest.py

extra_dist = Makefile

dist_files = $(python_files) $(extra_dist)

all: default-all default-subdirs

clean: default-clean

dist: default-dist

install: default-install

include ../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
