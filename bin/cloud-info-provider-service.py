#!/usr/bin/env python

import inspect
import os
import sys

# realpath() will make your script run, even if you symlink it :)
cmd_folder = os.path.abspath(os.path.split(
    os.path.realpath(inspect.getfile(inspect.currentframe())))[0])
cmd_folder = os.path.split(cmd_folder)[0]
if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)
os.chdir(cmd_folder)

import cloud_info.core
cloud_info.core.main()
