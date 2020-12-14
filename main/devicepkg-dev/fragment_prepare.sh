#!/bin/sh

if [ -z "$_outdir" ]; then
	_outdir="."
fi

# shellcheck disable=SC2154
if [ -z "$_config" ]; then
	_config="$_kconfig_name"."$CARCH"
fi

[ -z "$HOSTCC" ] || _hostcc="HOSTCC=$HOSTCC"

mkdir -p "$builddir/$_outdir"
# shellcheck disable=SC2086,SC2154
cp "$srcdir/$_config" "$builddir"/"$_outdir"/"$_config"
cp /home/pmos/build/pmos.config "$builddir"/"$_outdir"/pmos.config
make -C "$builddir" ARCH="$_carch" O="$_outdir" $_hostcc $_kconfig_name "$_outdir"/pmos.config
cp "$builddir"/"$_outdir"/.config "$builddir"/"$_outdir"/.config.old
KCONFIG_CONFIG="$builddir"/"$_outdir"/.config mergeconfig -m "$builddir"/"$_outdir"/.config "$builddir"/"$_outdir"/"$_config"
chmod 644 "$builddir"/"$_outdir"/.config
