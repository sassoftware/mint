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


.PHONY: all install $(generated_files)


all: default-all $(generated_files)

install: default-install
	# Empty target directories for custom configuration.
	mkdir -p $(DESTDIR)/etc/rmake/node.d
	mkdir -p $(DESTDIR)/srv/rbuilder/config/config.d
	# Install stubs to be overwritten by setup and/or rAPA.
	# (InitialContents, possibly group-writable w/ Ownership)
	install -D -m0664 noderc.rapa \
		$(DESTDIR)/etc/rmake/node.d/25_rbuilder-rapa.conf
	# "dot-keep" files to preserve the empty config directories.
	# This is marginally simpler than policy as long as the
	# dirs are root-owned, and keeps everything in one place.
	touch $(DESTDIR)/srv/rbuilder/config/config.d/.keep.rbuilder

clean: default-clean


include ../../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
