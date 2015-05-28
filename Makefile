#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


# may be adjusted by recipe (via make commandline)
export DESTDIR =	/
export PRODUCT =	rbuilder
export VERSION =	8
export SHORTVER =	$(VERSION)
export TOPDIR =		$(shell pwd)
export PREFIX =		/usr
export lib =		$(shell uname -m | sed -r '/x86_64|ppc64|s390x|sparc64/{s/.*/lib64/;q};s/.*/lib/')
export LIBDIR =		$(PREFIX)/$(lib)
export POSTGRES_VERSION = 9.0

# from here on shouldn't need overriding
export PYTHON = /usr/bin/python
export PYVER = $(shell $(PYTHON) -c 'import sys; print sys.version[0:3]')
export PYDIR = $(LIBDIR)/python$(PYVER)/site-packages

SUBDIRS = mint scripts rmake_plugins distro twisted ha puppet

.PHONY: mint_test $(generated_files)

## Standard rules
all: $(generated_files) default-subdirs

install: install-subdirs

clean: clean-subdirs default-clean


include Make.rules

# vim: set sts=8 sw=8 noexpandtab :
