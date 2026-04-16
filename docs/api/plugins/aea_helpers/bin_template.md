<a id="plugins.aea-helpers.aea_helpers.bin_template"></a>

# plugins.aea-helpers.aea`_`helpers.bin`_`template

PyInstaller entry point template for agent runner binaries.

Copy this file into your agent repo as ``pyinstaller/agent_bin.py`` and use it
as the ``--onefile`` entry point for PyInstaller.  It patches AEA's
configuration path handling for the frozen ``sys._MEIPASS`` environment and
imports all modules that PyInstaller needs to bundle.

This file is NOT meant to be executed or linted in the aea-helpers context.

