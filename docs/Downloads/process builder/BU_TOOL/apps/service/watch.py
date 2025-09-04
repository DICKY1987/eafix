# Optional watcher skeleton (no runtime loop here to keep import-safe)
def start_background_watch(path: str = ".", patterns: str = "*.yaml", debounce_ms: int = 500):
    return {"status": "stub-started", "path": path, "patterns": patterns, "debounce_ms": debounce_ms}