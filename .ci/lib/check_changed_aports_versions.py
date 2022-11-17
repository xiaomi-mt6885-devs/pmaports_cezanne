#!/usr/bin/env python3
# Copyright 2022 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later

import glob
import logging
import os
import subprocess
import sys
import tempfile

# Same dir
import common

# pmbootstrap
import add_pmbootstrap_to_import_path  # noqa
import pmb.parse
import pmb.parse.version
import pmb.helpers.logging


def get_package_version_sources(args, package, revision, check=True):
    """
    Get the version ($pkgver-r$pkgrel), checksums and a list of remote files
    (not bundled with the APKBUILD) from a specific git revision.
    :param package: name of the package
    :param revision: git revision to look at
    :param check: complain if the file does not exist
    :returns: {"checksums": see lib.common.parse_apkbuild_checksums(),
               "pkgrel": 3,
               "pkgver": "1.0.0",
               "sources_remote": ["x-1.0.0-r2.tar.bz2", ...],
               "version": "1.0.0-r2"}
    """
    # Redirect stderr to /dev/null, so git doesn't complain about files not
    # existing in upstream branch for new packages
    stderr = None
    if not check:
        stderr = subprocess.DEVNULL

    # Run something like "git show upstream/master:main/hello-world/APKBUILD"
    pmaports_dir = common.get_pmaports_dir()
    pattern = pmaports_dir + "/**/" + package + "/APKBUILD"
    path = glob.glob(pattern, recursive=True)[0][len(pmaports_dir + "/"):]
    apkbuild_content = common.run_git(["show", revision + ":" + path], check,
                                      stderr)
    if not apkbuild_content:
        return None

    # Save APKBUILD to a temporary path and parse it from there. (Not the best
    # way to do things, but good enough for this CI script.)
    with tempfile.TemporaryDirectory() as tempdir:
        apkbuild_path = f"{tempdir}/APKBUILD"
        with open(apkbuild_path, "w", encoding="utf-8") as handle:
            handle.write(apkbuild_content)
        parsed = pmb.parse.apkbuild(apkbuild_path, False, False)
        checksums = common.parse_apkbuild_checksums(args, apkbuild_path)

    # Build sources_remote from files in checksums that are not bundled.
    # To make the logic not overly complicated, only glob in the currently
    # checked out directory. This is inaccurate for the previous commit, but
    # good enough for how it's used in check_versions() below.
    sources_remote = []
    for filename, checksum in checksums.items():
        bundled_path_pattern = f"{os.path.dirname(path)}/**/{filename}"
        if not glob.glob(bundled_path_pattern, recursive=True):
            sources_remote += filename

    return {"checksums": checksums,
            "pkgrel": int(parsed['pkgrel']),
            "pkgver": parsed['pkgver'],
            "sources_remote": sources_remote,
            "version": f"{parsed['pkgver']}-r{parsed['pkgrel']}"}


def version_compare_operator(result):
    """ :param result: return value from pmb.parse.version.compare() """
    if result == -1:
        return "<"
    elif result == 0:
        return "=="
    elif result == 1:
        return ">"

    raise RuntimeError("Unexpected version_compare_operator input: " + result)


def exit_with_error_message():
    branch = common.get_upstream_branch()
    logging.error("")
    logging.error("NOTE: use 'pmbootstrap ci commits' to run this check"
                  " on your PC.")
    logging.error("")
    logging.error("Some more hints:")
    logging.error(f"* You may need to rebase on {branch}.")
    logging.error("* Detailed rules for bumping pkgrel/pkgver:")
    logging.error("  https://postmarketos.org/howto-bump-pkgrel-pkgver")
    logging.error("* If the error doesn't make sense (e.g. you want to")
    logging.error("  intentionally downgrade a package), add [ci:skip-build]")
    logging.error("  with reasoning to the last commit message.")
    logging.error("")
    logging.error("Thank you and sorry for the inconvenience.")
    exit(1)


def check_versions(args, packages):
    error = False

    # Get relevant commits: compare HEAD against upstream branch or HEAD~1
    # (the latter if this CI check is running on upstream branch). Note that
    # for the common.get_changed_files() code, we don't check against
    # upstream branch HEAD, but against the latest common ancestor. This is not
    # desired here, since we already know what packages changed, and really
    # want to check if the version was increased towards *current* upstream
    # branch HEAD.
    commit = f"upstream/{common.get_upstream_branch()}"
    if common.run_git(["rev-parse", "HEAD"]) == common.run_git(["rev-parse",
                                                                commit]):
        logging.info(f"NOTE: {commit} is on same commit as HEAD, comparing"
                     " HEAD against HEAD~1.")
        commit = "HEAD~1"

    for package in packages:
        logging.info("")
        # Get versions and sources, skip new packages
        head = get_package_version_sources(args, package, "HEAD")
        head_v = head["version"]
        upstream = get_package_version_sources(args, package, commit, False)
        if not upstream:
            if head["pkgrel"] != 0:
                logging.error(f"- {package}: {head_v} (HEAD) (new package)")
                logging.error("  ERROR: new package should have pkgrel=0")
                error = True
            else:
                logging.info(f"- {package}: {head_v} (HEAD) (new package)")
            continue
        upstream_v = upstream["version"]

        # Compare head and upstream versions based on rules from:
        # https://postmarketos.org/howto-bump-pkgrel-pkgver
        error_str = ""
        if head["sources_remote"]:
            if head["sources_remote"] == upstream["sources_remote"]:
                pkgver = upstream["pkgver"]
                pkgrel = upstream["pkgrel"] + 1
                if head["pkgver"] != pkgver or head["pkgrel"] != pkgrel:
                    error_str = f"expected pkgver={pkgver}, pkgrel={pkgrel}" \
                                " (pkgver unchanged, pkgrel + 1), because" \
                                " this package has unchanged remote sources"
            else:  # remote sources changed
                if upstream["pkgver"] == "9999":
                    pkgver = "9999"
                    pkgrel = upstream["pkgrel"] + 1
                    if head["pkgver"] != pkgver or head["pkgrel"] != pkgrel:
                        error_str = f"expected pkgver={pkgver}," \
                                    f" pkgrel={pkgrel} (pkgver unchanged," \
                                    " pkgrel + 1), because this package has" \
                                    " pkgver=9999"
                elif head["pkgver"] == upstream["pkgver"] or head["pkgrel"] != 0:
                    error_str = "expected pkgver to change and pkgrel=0," \
                                " because this package has changed remote" \
                                " sources"
        else:  # no remote sources
            if head["checksums"] == upstream["checksums"]:
                pkgver = upstream["pkgver"]
                pkgrel = upstream["pkgrel"] + 1
                if head["pkgver"] != pkgver or head["pkgrel"] != pkgrel:
                    error_str = f"expected pkgver={pkgver}, pkgrel={pkgrel} " \
                                " (pkgver unchanged, pkgrel + 1), because" \
                                " this package has no remote sources and the" \
                                " bundled sources didn't change"
            else:  # checksums changed
                if head["pkgver"] == upstream["pkgver"] or head["pkgrel"] != 0:
                    error_str = "expected pkgver to change and pkgrel=0," \
                                " because this package has no remote sources" \
                                " but the bundled files changed"

        result = pmb.parse.version.compare(head_v, upstream_v)
        if result != 1:
            error_str = "new version is not higher than the previous version"

        # Print result line ("- hello-world: 1-r2 (HEAD) > 1-r1 (HEAD~1)")
        formatstr = "- {}: {} (HEAD) {} {} ({})"
        operator = version_compare_operator(result)
        logging.error(formatstr.format(package, head_v, operator, upstream_v,
                                       commit))

        # Detailed error message should help the user to resolve it and explain
        # why it failed.
        if error_str:
            logging.error(f"  ERROR: {error_str}")
            error = True

    if error:
        exit_with_error_message()


if __name__ == "__main__":
    # Get and print modified packages
    common.add_upstream_git_remote()
    packages = common.get_changed_packages()
    logging.info(f"Changed packages: {packages}")

    # Verify modified package count
    common.get_changed_packages_sanity_check(len(packages))
    if len(packages) == 0:
        logging.info("no aports changed in this branch")
        exit(0)

    # Potentially skip this check
    if common.commit_message_has_string("[ci:skip-vercheck]"):
        logging.warning("WARNING: not checking for changed package versions"
                        " ([ci:skip-vercheck])!")
        exit(0)

    # Initialize args (so we can use pmbootstrap's APKBUILD parsing)
    sys.argv = ["pmbootstrap.py", "chroot"]
    args = pmb.parse.arguments()
    pmb.helpers.logging.init(args)

    # Verify package versions
    logging.info("Checking changed package versions...")
    check_versions(args, packages)
