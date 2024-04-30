#!/usr/bin/env python3
# Copyright 2021 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later

import shutil
import sys
import os
import importlib
import importlib.util
from site import getsitepackages


def path_pmbootstrap():
    """ Find the pmbootstrap installation folder, so we can import the Python
        code from there.
        returns: pmbootstrap installation folder
    """
    # This variable is set by pmbootstrap 1.52 and later
    # If it's undefined, try to find 'pmbootstrap' in path
    bin = os.environ.get("PMBOOTSTRAP_CMD") or shutil.which("pmbootstrap")

    if not bin:
        print("ERROR: 'pmbootstrap' not found in $PATH")
        sys.exit(1)

    # Resolve the symlink and verify the folder
    directory = os.path.dirname(os.path.realpath(bin))
    if os.path.exists(directory + "/pmb/__init__.py"):
        return directory

    directories = getsitepackages()
    for directory in directories:
        if os.path.exists(directory + "/pmb/__init__.py"):
            return directory

    # Symlink not set up properly
    print("ERROR: unable to find path to pmbootstrap.py. Try setting 'PMBOOTSTRAP_CMD'.")
    sys.exit(1)


# Check if pmb module can be imported
if importlib.util.find_spec("pmb") is None:
    # Add pmbootstrap dir to import path
    sys.path.append(os.path.realpath(path_pmbootstrap()))
