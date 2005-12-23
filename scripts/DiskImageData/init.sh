#!/bin/bash -x
# A quick script to setup an image
mount -n -t proc /proc /proc
mount -n -t sysfs /sys /sys

#/bin/dmesg -n level
[ -x /sbin/start_udev ] && /sbin/start_udev

state=`LC_ALL=C awk '/ \/ / && ($3 !~ /rootfs/) { print $4 }' /proc/mounts`
[ "$state" != "rw" -a "$READONLY" != "yes" ] && mount -n -o remount,rw /

mount -n /dev/pts

#Make the uml devices
mknod /dev/ubda b 98 0
mknod /dev/ubda1 b 98 1

# Clear mtab
(> /etc/mtab) &> /dev/null

# Enter mounted filesystems into /etc/mtab
mount -f /
mount -f /proc >/dev/null 2>&1
mount -f /sys >/dev/null 2>&1
mount -f /dev/pts >/dev/null 2>&1

#turn on swap
/sbin/swapon -a -e

for i in pre-tag-scripts tag-scripts post-tag-scripts kernel-tag-scripts post-kernel-tag-scripts; do
    [ -f /tmp/$i ] && /bin/sh /tmp/$i && rm /tmp/$i
done

#clean up the ubd devices
rm /dev/ubda1
rm /dev/ubda

umount /dev/pts
umount /sys

# we cannot remount while this script itself is still open, so
# use this exec to go to a shell that has its script provided
# entirely on the command line

exec /bin/bash -x -c 'rm -rf /tmp/*; mount -n -o remount,ro / || echo s > /proc/sysrq-trigger && echo u > /proc/sysrq-trigger && echo s > /proc/sysrq-trigger ; /sbin/halt -f -p'

