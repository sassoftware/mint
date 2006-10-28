#!/bin/sh
#
# Copyright (C) 2006 rPath, Inc.
# All Rights Reserved
#

X86_FLAVOR='~X, ~!alternatives, !bootstrap, ~builddocs,~buildtests, ~desktop, ~dietlibc, ~emacs, ~gcj,~gnome, ~gtk, ~ipv6, ~kde, ~krb, ~ldap, ~nptl,pam, ~pcre, ~perl, ~!pie, ~python, ~qt,~readline, ~!sasl, ~!selinux, ssl, ~tcl,tcpwrappers, ~tk, ~!xen, ~!xfce is: x86(~cmov,~i486, ~i586, ~i686, ~mmx, ~sse, ~sse2)'
DATE=$(date +%Y_%m_%d)

function carp {
    echo "snapshot build failed"
    exit 1
}

function carp_rmake {
    jobid=$1
    nail -s 'rBuilder Snapshot Build Failed' $ERROR_MAIL << EOT
The rBuilder appliance build failed:

$(rmake q $jobid --logs)
EOT
exit 1
}

function rewrite_version {
    file=$1
    newver=$2

    sed -ri "s/(\s+)version \= '.+'/\1version \= \'$newver\'/" $file
}

function merge() {
    pushd $RECIPES_PATH
    [ -d $RECIPES_PATH/$1/ ] || cvc co $1
    pushd $1
    cvc merge
    rewrite_version $1.recipe $DATE
    popd
    popd
}

function commit() {
    pushd $RECIPES_PATH/$1
    cvc commit --message "automated commit for $DATE"
    # [ $? != 0 ] && carp
    popd
}

function cook() {
    # make sure we're in the contexted directory
    pushd $RECIPES_PATH
    cvc cook $1 || carp
    popd
}

function merge_and_cook() {
    merge $1
    commit $1
    cook $1
}

function create_build() {
    project=$1; shift
    trove=$1; shift
    type=$1; shift

    TROVESPEC=$(conary rq --install-label $NIGHTLY_LABEL $trove --full-versions --flavors)
    eval $($CMDLINE_PATH/rbuilder build-create $project "$TROVESPEC" $type "$@")
}

function fetch_build() {
    target_recipe=$1
    target_file=$2

    pushd $RECIPES_PATH/$target_recipe
    URL=$($CMDLINE_PATH/rbuilder build-url $BUILD_ID)
    curl -L -o $target_file $URL
    popd
}

function get_mint_version {
    CHECKOUT_PATH=/srv/rbuilder/code/mint/
    MINT_VERSION=$(python -c "import sys; sys.path.append(\"$CHECKOUT_PATH\"); from mint import constants; print constants.mintVersion")
}

function create_mint_snapshot {
    get_mint_version

    pushd $CHECKOUT_PATH
    make product || carp
    rewrite_version $RECIPES_PATH/rbuilder/rbuilder.recipe $DATE
    popd
    pushd $RECIPES_PATH/rbuilder/
    cvc remove rbuilder-*.tar.bz2
    mv $CHECKOUT_PATH/rbuilder-$MINT_VERSION.tar.bz2 rbuilder-$DATE.tar.bz2
    cvc add rbuilder-$DATE.tar.bz2
    commit rbuilder
    popd
}
