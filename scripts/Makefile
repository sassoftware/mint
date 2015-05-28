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


static_files =				\
	add-lvm-disk			\
	add-rmake3-node			\
	dump-rbuilder-databases		\
	deleteproject			\
	generate-certs.sh		\
	group-script			\
	mcp-stack			\
	migrate-all-projects		\
	post-install			\
	preconfigure			\
	rbuilder-debug			\
	rmake-reset			\
	rmake-setup.pp			\
	set-authuserpass		\
	set-password			\
	update-package-index		\
	update-package-index-external	\
	$(generic_scripts)		\


generated_files = $(generic_scripts)

generic_scripts = \
	job-cleanup			\
	mint-admin			\
	mirror-inbound			\
	mirror-outbound			\
	pki-tool			\
	postgres-auto-update		\
	postgres-major-migrate		\
	process-system-events		\
	rbuilder-database		\
	repository-sync			\


override STATICDEST = /usr/share/rbuilder/scripts

all: default-all $(generated_files)

install: static-install default-install

clean: default-clean


$(generic_scripts): generic-script.py Makefile
	sed -e 's/some_module/$(subst -,_,$@)/g' $< >$@
	@chmod 0755 $@


include ../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
