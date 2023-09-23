#!/bin/sh

# shellcheck disable=SC2154
# shellcheck disable=SC3046
# shellcheck disable=SC2035
# shellcheck disable=SC1090

echo "searching for FIT images..."

ramdisk_addr=0xa2000000
image_addresses_start=0x80000000
image_addresses=$image_addresses_start
image_number=0

doodfeed=0xedfe0dd0
if itest $ramdisk_addr <= 0xa6001000; then
	echo "true"
fi

if itest $ramdisk_addr >= 0xa0001000; then
	echo "false"
fi

while itest $ramdisk_addr <= 0xa6001000; do
	if itest *$ramdisk_addr == $doodfeed; then
		echo "address at $ramdisk_addr matches"
		if itest $image_number != 0; then
			echo "######## image $image_number found at $ramdisk_addr ########"
			iminfo $ramdisk_addr
			mw $image_addresses $ramdisk_addr 1
			setexpr image_addresses $image_addresses + 4
		fi
		setexpr image_number $image_number + 1
	fi
	setexpr ramdisk_addr $ramdisk_addr + 0x1000
done

if itest $image_number <= 1; then
	echo "No images found!"
fi

if itest "${key_vol_down}" -eq "1"; then
	echo "key down pressed, booting 2nd image"
	setexpr image_address $image_addresses_start + 4
	setexpr image_address *"$image_address"
	echo "image_address: $image_address"
	source "$image_address":bootscript
else
	echo "key down NOT pressed, booting 1st image"
	setexpr image_address $image_addresses_start
	setexpr image_address *"$image_address"
	echo "image_address: $image_address"
	source "$image_address":bootscript
fi
