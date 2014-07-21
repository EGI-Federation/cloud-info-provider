#!/usr/bin/env python

import os, sys, inspect

# realpath() will make your script run, even if you symlink it :)
cmd_folder = os.path.abspath(os.path.split(os.path.realpath(inspect.getfile( inspect.currentframe() )))[0])
cmd_folder = os.path.split(cmd_folder)[0]
if cmd_folder not in sys.path:
     sys.path.insert(0, cmd_folder)
os.chdir(cmd_folder)

import cloud_bdii.core
cloud_bdii.core.main()
