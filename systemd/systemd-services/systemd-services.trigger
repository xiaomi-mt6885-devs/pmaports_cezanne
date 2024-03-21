#!/bin/sh
# Because these service files are installed with install_if, they might
# get installed after some other package has tried to enable them.
# we provide an "rc-update" binary which wraps systemctl, it also makes
# a list of services that failed to enable so we can try them again
# now that everything has been installed.

if [ ! -e /run/rc-update.failed ]; then
    exit 0
fi

while read -r cmd service; do
    echo "=> $cmd $service"
    systemctl $cmd $service
done < /run/rc-update.failed

rm -f /run/rc-update.failed
