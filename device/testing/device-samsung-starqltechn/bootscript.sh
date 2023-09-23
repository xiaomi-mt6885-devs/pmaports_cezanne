#!/bin/sh

# shellcheck disable=SC2154

setenv bootargs 'console=tty1 loglevel=15 clk_ignore_unused'

bootm "$image_address"
