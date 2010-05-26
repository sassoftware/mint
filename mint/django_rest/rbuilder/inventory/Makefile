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

python_files =	$(wildcard *.py)

dist_files = Makefile $(python_files)
GENERATE_DS=generateDS.py
XSD_DIR=xsd

.PHONY: clean install $(generated_files)

all: $(generated_files) default-all

install: pyfiles-install default-install

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