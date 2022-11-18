#!/bin/sh

# shellcheck disable=SC2154

echo "Booting Android"
echo "searching for KASLR address..."

addr=0x80000000

until cmp "$relocaddr" "$addr" 0x100; do
	setexpr addr $addr + 0x1000
done
echo "KASLR address is 0x$addr"
setenv bootm_low "0x$addr"
setenv bootm_size 0x5000000

fdt addr "$prevbl_initrd_start_addr"
fdt set "/images/kernel" "load" "<0x$addr>"
fdt set "/images/kernel" "entry" "<0x$addr>"
fdt addr "$prevbl_fdt_addr"
fdt print "/chosen"
bootm "$image_address#standard $image_address#standard $prevbl_fdt_addr"
