#!/usr/bin/env python

# Copyright (C) 2018 Intel Corporation
#
# SPDX-License-Identifier: MIT

import os
import sys
import signal
import time

def handle_pdb(sig, frame):
    '''
    Opens a pdb session wherever the execution is happening.
    '''
    import pdb
    pdb.Pdb().set_trace(frame)

if __name__ == '__main__':

    #Open a pdb session if we get a SIGUSR1 signal:
    signal.signal(signal.SIGUSR1, handle_pdb)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cvat.settings.{}" \
        .format(os.environ.get("DJANGO_CONFIGURATION", "development")))
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)
