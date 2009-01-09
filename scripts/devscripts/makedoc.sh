#!/bin/bash
#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#
# makedoc.sh - create static xhtml or text from docbook xml files using xmlto(1)
#
file="userguide.xml"
globalent="./libs/global.ent"
output=txt
use="usage: $0 [-h|-t] [-x template] [-f file]"
xslfrag="./libs/html_txt.xsl"
templ=""

while getopts htx:f: opt
do
    case "$opt" in
      t) output="txt";;
      h) output="xhtml-nochunks";;
      f) file="$OPTARG";;
      x) templ="-x $OPTARG";;
      \?)
         echo >&2 \
    $use
         exit 1;;
    esac
done
shift `expr $OPTIND - 1`

xmlto $templ $output $file
