#!/bin/sh

# Generate the contents for /etc/machine-info
generate_machine_info()
{
	machine_info=$1

	# shellcheck disable=SC2154
	{
		local model="${deviceinfo_name#"${deviceinfo_manufacturer}" *}"
		echo "PRETTY_HOSTNAME=\"$deviceinfo_name\""
		echo "CHASSIS=\"$deviceinfo_chassis\""
		echo "HARDWARE_VENDOR=\"$deviceinfo_manufacturer\""
		echo "HARDWARE_MODEL=\"$model\""
	} > "$machine_info"
}
