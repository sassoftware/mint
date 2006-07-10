#
# Copyright (c) 2005 rpath, Inc.
#
# All Rights Reserved
#

SUBDIRS = repos admin docs setup

kid_files = \
	applianceSpotlight.kid	\
	conaryDevelCfg.kid	\
	conaryUserCfg.kid	\
	confirmEmail.kid	\
	confirm.kid		\
	cookGroup.kid		\
	editGroup.kid		\
	editProject.kid		\
	editProduct.kid		\
	editPubrelease.kid	\
	editrMake.kid		\
	error.kid		\
	forgotPassword.kid	\
	frontPage.kid		\
	groups.kid		\
	help.kid		\
	joinRequest.kid		\
	layout.kid		\
	library.kid		\
	mailingLists.kid	\
	maintenance.kid		\
	members.kid		\
	newGroup.kid		\
	newProject.kid		\
	newrMake.kid		\
	passwordReset.kid	\
	pickArch.kid		\
	project.kid		\
	projectPage.kid		\
	projects.kid		\
	register_active.kid	\
	register_conf.kid	\
	register.kid		\
	register_reconf.kid	\
	rejectJoinRequest.kid   \
	product.kid		\
	products.kid		\
	pubreleases.kid		\
	rMake.kid		\
	rMakeStatus.kid		\
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
	kidc --strip-dest-dir $$(pwd) $(kid_files)
	mkdir -p $(DESTDIR)$(mintdir)$(DIR)
	for f in $(kid_files) *.pyc; do \
                cp -a $$f $(DESTDIR)$(mintdir)$(DIR)/$$f; \
        done

dist: default-dist

clean: default-clean

include ../../../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
