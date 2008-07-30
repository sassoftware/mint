#!/bin/sh
DIR=`mktemp -d /tmp/collect-XXXXXX`
cd $DIR
/usr/sbin/pvdisplay > pvdisplay 2>&1
/usr/sbin/vgdisplay > vgdisplay 2>&1
/usr/sbin/lvdisplay > lvdisplay 2>&1
echo $DIR

