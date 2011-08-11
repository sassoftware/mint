#
# Copyright (c) 2009 rPath, Inc.
#
# This program is distributed under the terms of the Common Public License,
# version 1.0. A copy of this license should have been distributed with this
# source file in a file called LICENSE. If it is not present, the license
# is always available at http://www.rpath.com/permanent/licenses/CPL-1.0.
#
# This program is distributed in the hope that it will be useful, but
# without any warranty; without even the implied warranty of merchantability
# or fitness for a particular purpose. See the Common Public License for
# full details.
#

#SUBDIRS =	fixtures manager models_xsl docs
SUBDIRS = manager
python_files =	$(wildcard *.py)
template_files = $(wildcard *.html *.xsl)

dist_files = Makefile $(python_files)

.PHONY: clean install

all: default-all

install: pyfiles-install default-install
	mkdir -p $(DESTDIR)$(PYDIR)/$(PYDEST)

clean: default-clean

include ../../../../Make.rules
