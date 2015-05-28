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


SUBDIRS = admin

kid_files = $(wildcard *.kid)

python_files = __init__.py

all: kid-build default-all

install: kid-install pyfiles-install default-install

clean: kid-clean default-clean


include ../../../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
