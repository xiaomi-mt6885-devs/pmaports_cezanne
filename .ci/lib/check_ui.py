#!/usr/bin/env python3
# Copyright 2021 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later

import glob
import sys
import os

# Same dir
import common

import add_pmbootstrap_to_import_path
import pmb.parse


def check_aports_ui(args, pkgnames):
    """
    Raise an error if package in _pmb_recommends is not found
    """
    pmaports_cfg = pmb.config.pmaports.read_config(args)

    for arch in pmaports_cfg["supported_arches"].split(","):
        for pkg in pkgnames:
            path = os.path.join(args.aports, "main", pkg, "APKBUILD")
            apkbuild = pmb.parse.apkbuild(path)
            # Skip if arch isn't enabled
            if not pmb.helpers.package.check_arch(args, apkbuild["pkgname"], arch, False):
                continue

            for package in apkbuild["_pmb_recommends"]:
                depend = pmb.helpers.package.get(args, package,
                                                 arch, must_exist=False)
                if depend is None or not pmb.helpers.package.check_arch(args, package, arch):
                    raise RuntimeError(f"{path}: package '{package}' from"
                                       f" _pmb_recommends not found for arch '{arch}'")

            # Check packages from "_pmb_recommends" of -extras subpackage if one exists
            if f"{apkbuild['pkgname']}-extras" in apkbuild["subpackages"]:
                apkbuild = apkbuild["subpackages"][f"{apkbuild['pkgname']}-extras"]
                for package in apkbuild["_pmb_recommends"]:
                    depend = pmb.helpers.package.get(args, package,
                                                     arch, must_exist=False)
                    if depend is None or not pmb.helpers.package.check_arch(args, package, arch):
                        raise RuntimeError(f"{path}: package '{package}' from _pmb_recommends "
                                           f"of -extras subpackage is not found for arch '{arch}'")


if __name__ == "__main__":
    common.add_upstream_git_remote()
    pkgnames = common.get_changed_ui()

    if len(pkgnames) == 0:
        print("No UI packages changes in this branch")
        exit(0)

    print(f"Changed UI packages: {' '.join(pkgnames)}")

    # Initialize args (so we can use pmbootstrap's kconfig parsing)
    sys.argv = ["pmbootstrap", "kconfig", "check"]
    args = pmb.parse.arguments()
    pmb.helpers.logging.init(args)

    print("Checking changed UI packages...")
    last_failed = check_aports_ui(args, pkgnames)
    if last_failed:
        print(f"UI package check failed: {last_failed}")
        exit(1)
