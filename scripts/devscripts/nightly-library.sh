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

function merge() {
    pushd $RECIPES_PATH
    [ -d $RECIPES_PATH/$1/ ] || cvc co $1
    pushd $1
#    cvc merge
#    [ $? != 0 ] && carp
    echo "currently a no-op until merge is fixed"
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
    cvc cook $1
    [ $? != 0 ] && carp
    popd
}


function merge_and_cook() {
    merge $1
    commit $1
    cook $1
}


function create_build() {
    project=$1
    trove=$2
    type=$3
    options=$4

    TROVESPEC=$(conary rq $trove --full-versions --flavors)
    eval $($CMDLINE_PATH/rbuilder build-create $project "$TROVESPEC" $type $options)
}


function fetch_build() {
    target_recipe=$1
    target_file=$2

    pushd $RECIPES_PATH/$target_recipe
    URL=$($CMDLINE_PATH/rbuilder build-url $BUILD_ID)
    curl -L -o $target_file $URL
    popd
}
