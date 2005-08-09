#
# Copyright (c) 2005 rpath, Inc.
#
# All Rights Reserved
#

SUBDIRS = repos

kid_files = \
	editRelease.kid		\
	error.kid		\
	frontPage.kid		\
	layout.kid		\
	library.kid		\
	login.kid		\
	mailingLists.kid	\
	memberSettings.kid	\
	members.kid		\
	newProject.kid		\
	newRelease.kid		\
	projectDesc.kid		\
	project.kid		\
	projects.kid		\
	projectPage.kid		\
	register.kid		\
	register_conf.kid	\
	release.kid		\
	releases.kid		\
	searchResults.kid	\
	userInfo.kid		\
	userSettings.kid	\
	users.kid

python_files = __init__.py

extra_dist = Makefile

dist_files = $(extra_dist) $(kid_files) $(python_files)

all: default-all default-subdirs

install: kidfiles-install install-subdirs pyfiles-install

subdirs: default-subdirs

kidfiles-install:
	kidc --strip-dest-dir $$(pwd) $$(pwd)
	mkdir -p $(DESTDIR)$(mintdir)$(DIR)
	for f in $(kid_files) *.pyc; do \
                cp -a $$f $(DESTDIR)$(mintdir)$(DIR)/$$f; \
        done

dist: default-dist 

clean: default-clean

include ../../../Make.rules
