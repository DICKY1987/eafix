# eafix - APF Repo Skeleton

Generated from BU_* briefs: diagnostics schema, tests, CI, and app stubs.

## Project Structure

- `src/` – application source code (`eafix` package and submodules)
- `tests/` – unit tests
- `docs/` – documentation, reference material, and misc guides
- `settings.json` – example configuration
- Includes scaffolding for conditional probability signals, currency strength
  analytics, and transport failover examples used in tests
- `src/eafix/indicator_configs` – JSON indicator definitions that are loaded at
  runtime for plug‑and‑play extensibility. Add a new indicator by dropping a
  JSON config into this directory—no code changes required.
