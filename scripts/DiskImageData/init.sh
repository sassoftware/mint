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

#Link in the mouse
ln -s psaux /dev/mouse

# Clear mtab
(> /etc/mtab) &> /dev/null

# Enter mounted filesystems into /etc/mtab
mount -f /
mount -f /proc >/dev/null 2>&1
mount -f /sys >/dev/null 2>&1
mount -f /dev/pts >/dev/null 2>&1

#turn on swap
/sbin/swapon -a -e

for i in pre-tag-scripts conary-tag-script post-tag-scripts conary-kernel-tag-script post-kernel-tag-scripts; do
    [ -f /root/$i ] && /bin/sh /root/$i 2>&1 >> /root/conary-tag-scripts.output
done

rm -f /root/pre-tag-scripts
rm -f /root/post-tag-scripts
rm -f /root/post-kernel-tag-scripts

#Setup /etc/nsswitch and system-auth
/usr/bin/authconfig --kickstart --enablemd5 --enableshadow --disablecache

#Reset the root password to blank
/usr/sbin/usermod -p '' root

#Remove the blkid.tab file that causes the kernel to try to boot off of /dev/ubd0
#when in qemu/vmware
[ -f /etc/blkid.tab ] && rm /etc/blkid.tab

#clean up the ubd devices
rm /dev/ubda1
rm /dev/ubda

umount /dev/pts
umount /sys

# we cannot remount while this script itself is still open, so
# use this exec to go to a shell that has its script provided
# entirely on the command line

# no-halt option ensures script won't forcibly halt system if it is
# not the primary init called direcly by the kernel.
if [ "$1" != "no-halt" ]
then
  exec /bin/bash -x -c 'rm -rf /tmp/*; mount -n -o remount,ro / || echo s > /proc/sysrq-trigger && echo u > /proc/sysrq-trigger && echo s > /proc/sysrq-trigger ; /sbin/halt -f -p'
else
  umount /proc
  exec /bin/bash -x -c 'rm -rf /tmp/*; mount -n -o remount,ro /'
fi
