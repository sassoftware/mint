javascript_files =\
	ec2.js \
	filesystems.js \
	groupbuilder.js \
	library.js \
	mirror.js \
	rpc.js	\
	trovepicker.js \
	rmakebuilder.js \
	repobrowser.js

generated_files =\
	buildtypes.js \
	jobstatus.js  \
	buildtemplates.js

dist_files = $(javascript_files) $(generated_files) Makefile

all: $(javascript_files) $(generated_files)

buildtypes.js: ../../../buildtypes.py
	python ../../../buildtypes.py --genjs > buildtypes.js

jobstatus.js: ../../../jobstatus.py
	python ../../../jobstatus.py --genjs > jobstatus.js

buildtemplates.js: ../../../buildtemplates.py
	PYTHONPATH=../../../../ python ../../../buildtemplates.py --genjs > buildtemplates.js

install:
	mkdir -p $(DESTDIR)$(contentdir)/javascript
	for f in $(javascript_files) $(generated_files); do \
		install -m 644 $$f $(DESTDIR)$(contentdir)/javascript/$$f; \
	done

dist: default-dist

clean: default-clean

include ../../../../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
