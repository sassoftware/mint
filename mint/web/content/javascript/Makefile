javascript_files = $(wildcard *.js)

static_files = $(javascript_files)

all: default-all

install: static-install default-install

clean: default-clean
	rm -f $(generated_files)

include ../../../../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
