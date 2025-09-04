# eafix - APF Repo Skeleton

Generated from BU_* briefs: diagnostics schema, tests, CI, and app stubs.

## Project Structure

- `src/` – application source code (`eafix` package and submodules)
- `tests/` – unit tests
- `docs/` – documentation, reference material, and misc guides
- `settings.json` – example configuration
- Includes scaffolding for conditional probability signals, currency strength
  analytics, and transport failover examples used in tests

## Launching the desktop GUI with MetaTrader 4

Running the desktop application also launches a MetaTrader 4 terminal if the
`terminal.exe` executable can be located. The launcher checks the `MT4_PATH`
environment variable first and falls back to a couple of common installation
paths on Windows when running on that platform.

Two helper scripts are provided which can be placed on the desktop and used as
shortcuts:

- `launch_gui.bat` – Windows batch file
- `launch_gui.sh` – POSIX shell script

Both scripts simply execute `python -m eafix.apps.desktop.main` which in turn
starts MetaTrader 4 (if available) and then the Python GUI.
