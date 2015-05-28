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


doc_files = $(wildcard *.txt)

all: default-all

install: default-install
	mkdir -p $(DESTDIR)$(PYDIR)/$(PYDEST)
	find . -name "*.txt" | tar cf - . --files-from=- --no-recursion | tar xf - -C $(DESTDIR)$(PYDIR)/$(PYDEST)
	find $(DESTDIR)$(PYDIR)/$(PYDEST) -type d -exec chmod 0755 {} +
	find $(DESTDIR)$(PYDIR)/$(PYDEST) -type f -exec chmod 0644 {} +

clean: default-clean
	find . -name "*.txt" -delete
	find * -type d -exec rmdir -p --ignore-fail-on-non-empty {} +


include ../../../../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
