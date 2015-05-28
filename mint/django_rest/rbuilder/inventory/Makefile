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


SUBDIRS =	fixtures manager views
python_files =	$(wildcard *.py)

dist_files = Makefile $(python_files)
GENERATE_DS=generateDS.py
XSD_DIR=xsd

.PHONY: clean install $(generated_files)

all: $(generated_files) default-all

install: pyfiles-install default-install
	mkdir -p $(DESTDIR)$(PYDIR)/$(PYDEST)

clean: default-clean

generate: $(patsubst $(XSD_DIR)/%.xsd,rule-%,$(wildcard $(XSD_DIR)/*.xsd))

rule-%:
	$(GENERATE_DS) -f --silence \
                --no-dates \
                --no-versions \
                --member-specs=list \
                --external-encoding=utf-8 \
                --search-path=$(XSD_DIR) \
                -o generateds_$(subst -,_,$(patsubst rule-%,%,$@)).py \
                $(XSD_DIR)/$(patsubst rule-%,%,$@).xsd

install-generate: $(addprefix install-rule-,$(wildcard xml_*))

install-rule-%: %
	install -d $(DESTDIR)$(pydir)$<
	install $</*.py $(DESTDIR)$(pydir)$</

include ../../../../Make.rules
