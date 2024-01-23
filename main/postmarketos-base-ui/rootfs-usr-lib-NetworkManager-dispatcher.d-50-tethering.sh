#!/bin/sh -e
# shellcheck disable=SC1091
# Handle USB tethering with unudhcpd and NetworkManager while also
# keeping SSH login over USB working when tethering is disabled.
#
# Copyright (c) 2023 Dylan Van Assche
# SPDX-License-Identifier: GPL-3.0-or-later

# Must match with the supplied connection profile,
# using UUID allows the user to change the connection name if they want to.
con_uuid_networking="83bd1823-feca-4c2b-9205-4b83dc792e1f"
con_uuid_tethering="a870f58b-2581-4105-a3c8-d47638e9d879"
interface="usb0"

[ -e /etc/unudhcpd.conf ] && . /etc/unudhcpd.conf
host_ip="${unudhcpd_host_ip:-172.16.42.1}"
client_ip="${unudhcpd_client_ip:-172.16.42.2}"

# Skip if iface does not match
if [ "$DEVICE_IFACE" != "$interface" ]; then
	exit 0
fi

# Trigger a disconnect/connect event on the client side to request a new DHCP lease.
reactivate_gadget() {
	# Mount configFS
	mkdir -p /config
	mount -t configfs none /config || true

	logger -t nm-tethering "configFS mounted"

	# Reactivate gadget
	udc=$(cat /config/usb_gadget/g1/UDC)
	echo "" > /config/usb_gadget/g1/UDC
	sleep 1
	echo "$udc" > /config/usb_gadget/g1/UDC

	logger -t nm-tethering "gadget reactivated"

	# Unmount configFS
	umount /config
	rm -rf /config

	logger -t nm-tethering "configFS unmounted"
}

# Default static IP for SSH acccess
# 1. Configure NetworkManager connection to use IP 172.16.42.1, same as initfs.
# 2. Disable IPv6 as unudhcpd only supplies IPv4 addresses.
# 3. Start unudhcpd to handle DHCP requests.
# 4. Reactivate the USB Ethernet gadget to force the clients to reactivate the interface.
disable_tethering() {
	# Restart unudhpcd and configure it similar to initfs
	killall unudhpcd || true
	(unudhcpd -i "$interface" -s "$host_ip" -c "$client_ip") &
	logger -t nm-tethering "unudhcpd started"

	# Reactivate gadget to apply changes
	reactivate_gadget
	logger -t nm-tethering "USB tethering disabled"
}

# USB tethering
# 1. Enforce 172.16.42.1 as host IP even in tethering mode.
# 2. Stop unudhcpd as NetworkManager will spawn dnsmasq to handle DNS and DHCP requests.
# 3. Reactivate the USB Ethernet gadget to force the clients to reactivate the interface.
enable_tethering() {
	# Kill unudhcpd if needed
	killall unudhcpd || true
	logger -t nm-tethering "unudhcpd stopped"

	# Reactivate gadget to apply changes
	reactivate_gadget
	logger -t nm-tethering "USB tethering enabled"
}

con_name="$(nmcli -t device | grep "^$interface" | cut -d: -f4)"
if [ -n "$con_name" ]; then
	con_uuid="$(nmcli -t connection show "$con_name" | grep ^connection.uuid | cut -d: -f2)"
fi

# Enforce the IP range as when tethering is disabled, this will retrigger
# the script as we have to reapply again,
if [ -n "$con_uuid" ]; then
	ip=$(nmcli -t connection show "$con_uuid" | grep ^ipv4.addresses | cut -d: -f2)
	if [ "$ip" != "$host_ip/16" ]; then
		logger -t nm-tethering "Enforcing $host_ip/16 as DHCP range"
		nmcli connection modify "$con_uuid" ipv4.address "$host_ip/16"
		nmcli device reapply "$interface"
		exit
	fi
fi

# We only manage those system connections
case "$con_uuid" in
	"$con_uuid_networking")
		method=manual
		;;
	"$con_uuid_tethering")
		method=shared
		;;
esac

# Handle dispatcher events for tethering
case $NM_DISPATCHER_ACTION in
	# Always disable tethering on insert or removal for security
	"up"|"down")
		disable_tethering

		# The connection may have been configured before to tethering which
		# is not desired when iface comes up or is shut down as tethering must be
		# disabled. Enforce this by triggering a reapply after modifying the connection
		# which will cause NetworkManager to trigger the script again.
		# If the iface is already down since dispatcher scripts are executed async,
		# the command will fail which is fine to ignore
		if [ "$method" = "shared" ]; then
			logger -t nm-tethering "Enforcing tethering disabled on iface up/down"
			nmcli device reapply "$interface" || true
		fi
		;;
	# Enable tethering if the user explicitly enabled it
	"reapply")
		if [ "$method" = "shared" ]; then
			enable_tethering
		elif [ "$method" = "manual" ]; then
			disable_tethering
		fi
		;;
esac
