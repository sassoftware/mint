javascript_files =\
	ec2.js \
	filesystems.js \
	groupbuilder.js \
	library.js \
	mirror.js \
	newbuildsfromproductdefinition.js \
	rpc.js	\
	trovepicker.js \
	repobrowser.js \
	editversion.js \
	dialogs.js \
	jquery-1.2.3.min.js \
	jquery-1.2.6.min.js \
	jquery.ui-1.5.2.all.min.js \
	swfobject.js \
	swf_deeplink_history.js \
	whizzyupload.js

generated_files =\
	buildtypes.js \
	jobstatus.js  \
	buildtemplates.js

static_files = $(javascript_files) $(generated_files)

all: $(generated_files) default-all

install: static-install default-install

clean: default-clean
	rm -f $(generated_files)

buildtypes.js: ../../../buildtypes.py
	python ../../../buildtypes.py --genjs > buildtypes.js

jobstatus.js: ../../../jobstatus.py
	python ../../../jobstatus.py --genjs > jobstatus.js

buildtemplates.js: ../../../buildtemplates.py
	PYTHONPATH=../../../../ python ../../../buildtemplates.py --genjs > buildtemplates.js


include ../../../../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
