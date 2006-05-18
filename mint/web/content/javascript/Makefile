javascript_files =\
	generic.js \
	groupbuilder.js \
	library.js \
	mirror.js \
	rpc.js

generated_files =\
	releasetypes.js \
	jobstatus.js

dist_files = $(javascript_files) $(generated_files) Makefile

all: $(javascript_files) $(generated_files)

releasetypes.js: ../../../releasetypes.py
	python ../../../releasetypes.py --genjs > releasetypes.js

jobstatus.js: ../../../jobstatus.py
	python ../../../jobstatus.py --genjs > jobstatus.js

install:
	mkdir -p $(DESTDIR)$(contentdir)/javascript
	for f in $(javascript_files) $(generated_files); do \
		install -m 644 $$f $(DESTDIR)$(contentdir)/javascript/$$f; \
	done

dist: default-dist

clean: default-clean

include ../../../../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
