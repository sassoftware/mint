#
# Copyright (c) 2005 rpath, Inc.
#
# All Rights Reserved
#
SUBDIRS = server archive

python_files = \
               _apache.py \
               accounttest.py \
               authtest.py \
               cachetest.py \
               distrotest.py \
               grouptrovetest.py \
               helperfuncstest.py \
               htmltest.py \
               jobstest.py \
               joinrequesttest.py \
               labelstest.py \
               mint_rephelp.py \
               projecttest.py \
               recipes.py \
               releasetest.py \
               rephelp.py \
               repostest.py \
               reportstest.py \
               searchtest.py \
               sessionstest.py \
               tablestest.py \
               testsuite.py \
               xmltest.py \
               webtest.py

extra_dist = Makefile

dist_files = $(python_files) $(extra_dist)

all: default-all default-subdirs

clean: default-clean

dist: default-dist

install: default-install

include ../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
