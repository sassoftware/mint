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


SUBDIRS = server mint_archive

python_files = \
               _apache.py \
               accounttest.py \
               authtest.py \
               cachetest.py \
	       cmdlinetest.py \
               configtest.py \
               coverage.py \
               coveragewrapper.py \
	       ec2test.py \
               fixtures.py \
               grouptrovetest.py \
               helperfuncstest.py \
               htmltest.py \
               injectiontest.py \
               jobserverharness.py \
               joinrequesttest.py \
               labelstest.py \
               marketingtest.py	\
               mint_rephelp.py \
               mirrortest.py \
               buildtest.py \
               projecttest.py \
	       productversiontest.py \
               pubreleasetest.py \
               recipes.py \
               repostest.py \
               reportstest.py \
               schematest.py \
               searchtest.py \
               sessionstest.py \
               spidertest.py \
               testsuite.py \
	       updateservicetest.py \
               usertest.py \
               xmltest.py \
               webtest.py \
	       webhandlertest.py \
               webmemberstest.py \
	       websetuptest.py \
	       webrepostest.py \
	       webprojecttest.py

extra_dist = Makefile

dist_files = $(python_files) $(extra_dist)

all: default-all default-subdirs

clean: default-clean

dist: default-dist

install: default-install

include ../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
