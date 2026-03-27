# SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-Duilio-Commercial
#
# Deprecated compatibility wrapper.
# Please use airfoil_tools.py instead.

from runpy import run_path
from pathlib import Path

if __name__ == "__main__":
    run_path(str(Path(__file__).with_name("airfoil_tools.py")), run_name="__main__")
