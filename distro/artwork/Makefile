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

# NB: This Makefile does not regenerate artwork as that is rarely
# needed and it would bloat build dependencies greatly.

SUBDIRS = anaconda_legacy

.PHONY: all install clean


all: default-all

install: default-install
	install -D -m0644 anaconda_first.png $(DESTDIR)/usr/share/anaconda/pixmaps/progress_first.png
	install -D -m0644 anaconda_splash.png $(DESTDIR)/usr/share/anaconda/pixmaps/splash.png
	install -D -m0644 bootloader_splash.png $(DESTDIR)/boot/extlinux/rbuilder_background.png
	install -D -m0644 splashy_background.png $(DESTDIR)/usr/share/splashy/themes/rbuilder/background.png

clean: default-clean


include ../../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
