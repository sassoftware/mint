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

all: default-all 

constants.py: ../Makefile ../Make.defs Makefile
	sed -e s,@version@,$(VERSION),g \
	$< > $@

install: all pyfiles-install default-install install-generate
	$(PYTHON) -c "import compileall; compileall.compile_dir('$(DESTDIR)$(pydir)', ddir='$(pydir)', quiet=1)"
	$(PYTHON) -OO -c "import compileall; compileall.compile_dir('$(DESTDIR)$(pydir)', ddir='$(pydir)', quiet=1)"

dist: default-dist

clean: default-clean

GENERATE_DS=/home/jslagle/rpath-hg/generateDS/generateDS.py
xmlDir = $(subst .,_,$(patsubst rule-%,xml_%,$(1)))
xmlVer = $(patsubst rule-%,%,$(1))

generate: $(patsubst ../xsd/system-%.xsd,rule-%,$(wildcard ../xsd/system-*.xsd))

rule-%:
	mkdir -p $(call xmlDir,$@)
	touch $(call xmlDir,$@)/__init__.py
	$(GENERATE_DS) -f --silence \
                --no-dates \
                --no-versions \
                --member-specs=list \
                --super=supers_system \
                --external-encoding=utf-8 \
                -o $(call xmlDir,$@)/supers_system.py \
                -s $(call xmlDir,$@)/system.py \
                --user-methods=gends_user_methods \
                ./xsd/system-$(call xmlVer,$@).xsd

install-generate: $(addprefix install-rule-,$(wildcard xml_*))

install-rule-%: %
	install -d $(DESTDIR)$(pydir)$<
	install $</*.py $(DESTDIR)$(pydir)$</

include ../../../../Make.rules
