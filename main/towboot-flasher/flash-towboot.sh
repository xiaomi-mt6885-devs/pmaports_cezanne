#!/bin/sh

flash_emmc() {
	echo 0 > /sys/block/mmcblk2boot0/force_ro
	dd if=/usr/share/towboot-flasher/Tow-Boot.mmcboot.bin of=/dev/mmcblk2boot0 bs=4k
	echo 1 > /sys/block/mmcblk2boot0/force_ro
}

flash_spi() {
	# TODO: implement
	echo "Flashing SPI!"
}


if [ ! -f /etc/deviceinfo ]; then
	echo "This does not seem to be a postmarketOS installation, exiting"
	exit 0
fi

device_string=$(grep codename /etc/deviceinfo  | grep codename | cut -d = -f 2 | cut -d \" -f 2)

case "$device_string" in
	"*pinephone")
		flash_emmc
		;;
	"*pinebookpro"|"*rockpro64")
		flash_spi
		;;
	*)
		echo "This device is not supported by this script"
		exit 1
		;;
esac

