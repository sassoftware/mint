#
# Copyright (c) 2005 rpath, Inc.
#
# All Rights Reserved
#

SUBDIRS = repos admin docs

kid_files = \
	conaryCfg.kid		\
	confirmEmail.kid	\
	confirm.kid		\
	editProject.kid		\
	editRelease.kid		\
	error.kid		\
	forgotPassword.kid	\
	frontPage.kid		\
	joinRequest.kid		\
	layout.kid		\
	library.kid		\
	loginLanding.kid	\
	mailingLists.kid	\
	members.kid		\
	newProject.kid		\
	newRelease.kid		\
	passwordReset.kid	\
	project.kid		\
	projectPage.kid		\
	projects.kid		\
	register_active.kid	\
	register_conf.kid	\
	register.kid		\
	register_reconf.kid	\
	rejectJoinRequest.kid   \
	release.kid		\
	releases.kid		\
	rss20.kid		\
	searchResults.kid	\
	uploadKey.kid		\
	userInfo.kid		\
	userSettings.kid	\
	users.kid		\
	viewJoinRequest.kid

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
