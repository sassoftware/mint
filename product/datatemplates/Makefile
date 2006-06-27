#
# Copyright (c) 2005 rpath, Inc.
#
# All Rights Reserved
#

SUBDIRS =

dist_files =

python_files = usertemplates.py

all: default-subdirs

install: install-subdirs

subdirs: default-subdirs

dist: defaultdist dist-subdirs

# only datatemplates are allowed to override initial python files.
defaultdist: $(dist_files)
	cp -a usertemplates.py $(DISTDIR)/mint/usertemplates.py

clean: default-clean clean-subdirs

include ../../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
