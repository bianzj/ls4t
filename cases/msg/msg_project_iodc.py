#!/usr/bin/env python3
"""Compatibility entry point for IODC MSG LST projection."""

from cases.msg.msg_project_hdf5 import main


if __name__ == "__main__":
    main("iodc-lst")
