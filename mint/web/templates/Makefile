#
# Copyright (c) 2005 rpath, Inc.
#
# All Rights Reserved
#

kid_files = \
	editRelease.kid		\
	error.kid		\
	frontPage.kid		\
	layout.kid		\	
	library.kid		\
	login.kid		\
	memberSettings.kid	\
	members.kid		\
	newProject.kid		\
	newRelease.kid		\
	projectDesc.kid		\
	projectPage.kid		\
	register.kid		\
	release.kid		\
	releases.kid		\
	searchResults.kid	\
	userInfo.kid		\
	userSettings.kid

extra_dist = Makefile

dist_files = $(extra_dist) $(kid_files)

all: default-all

install: kidfiles-install

kidfiles-install:
	kidc --strip-dest-dir $$(pwd) $$(pwd)
	mkdir -p $(DESTDIR)$(mintdir)$(DIR)
	for f in $(kid_files) *.pyc; do \
                cp -a $$f $(DESTDIR)$(mintdir)$(DIR)/$$f; \
        done

dist: default-dist

clean: default-clean

include ../../../Make.rules
