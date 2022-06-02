#!/bin/sh -uex

# Tequila boards run a ghetto U-Boot hackfest that reads the kernel from a fixed location in memory, and only expects
# it to be a legacy U-Boot kernel image, it's assumed that the necessary initramfs is *inside* the image file.
# So we do a similar thing to the "isorec" trick seen elsewhere. The kernel initramfs has a small busybox shim to
# grab the initramfs from a magical place in flash memory, that lies within the 14mb space available for the kernel.

# The seek puts the initramfs 10mb after the starting point of the kernel.
# It follows that this hack assumes the kernel image is less than 10mb, and the initramfs is less than 4mb.
dir=$(dirname $1)
dd if=$dir/initramfs bs=512 of=$dir/uImage seek=20480

# This whole approach should be considered a temporary measure. Ideally a recent U-Boot is brought up on the device so
# that modern fastboot + Android boot.img support becomes possible, and all the ugly shims go away.
