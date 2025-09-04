#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Windows-friendly repository ingester for the HUEY_P organizer DB.
Now supports a per-repo config file (JSON or YAML) to customize:
- exclude patterns (dirs/globs)
- component mapping (folder keywords, glob/regex rules)
- category overrides by extension
- tag rules (static, by extension, by folder keyword)
- default hash size limit

Usage (PowerShell):
  python repo_ingester.py C:\Projects\HUEY_P --db C:\path\to\huey_project_organizer.db --config C:\path\to\repo.config.json -v
  python repo_ingester.py . --config repo.config.yaml --max-hash-mb 8

If both CLI flags and config provide the same setting, CLI wins.
"""
import argparse, os, sqlite3, hashlib, json, re, sys, time, datetime as dt, fnmatch
from pathlib import Path

try:
    import yaml  # optional
except Exception:
    yaml = None

# ---- Defaults (can be overridden by config) ----
DEFAULT_DB = r"/mnt/data/huey_project_organizer.db"
DEFAULT_EXCLUDES = {'.git', '__pycache__', '.venv', 'node_modules', '.idea', '.vscode', 'dist', 'build', '.mypy_cache', '.ruff_cache'}
DEFAULT_AUTO_COMPONENT_MAP = {
    "mql4": "MT4 Execution Engine",
    "experts": "MT4 Execution Engine",
    "include": "MT4 Execution Engine",
    "indicators": "Signal Framework",
    "mt4_dde_interface": "Communication Bridge",
    "dde": "Communication Bridge",
    "core": "Python GUI Hub",
    "tabs": "Python GUI Hub",
    "widgets": "Python GUI Hub",
    "database": "Matrix & Parameter Manager",
    "matrix": "Matrix & Parameter Manager",
    "organized": "Configuration & Schemas",
    "schemas": "Configuration & Schemas",
    "config": "Configuration & Schemas",
    "configuration": "Configuration & Schemas",
    "testing": "Testing & Validation",
    "tests": "Testing & Validation",
    "docs": "Configuration & Schemas",
    "documentation": "Configuration & Schemas",
    "calendar": "Economic Calendar Module",
    "economic_calendar": "Economic Calendar Module",
    "data": "Data & Logging",
    "logs": "Data & Logging",
    "backups": "Data & Logging",
}
CATEGORY_ORDER = ["schema","config","test","script","code","doc","data","log","binary","other"]

# ---- Helpers ----
def sha256sum(path, max_bytes=None, chunk=1024*1024):
    h = hashlib.sha256()
    read = 0
    with open(path, "rb") as f:
        while True:
            chunkb = f.read(chunk)
            if not chunkb:
                break
            h.update(chunkb)
            read += len(chunkb)
            if max_bytes and read >= max_bytes:
                break
    return h.hexdigest()

def iso_utc(ts):
    return dt.datetime.utcfromtimestamp(ts).strftime("%Y-%m-%dT%H:%M:%SZ")

def to_norm(path: Path) -> str:
    # forward slashes + lowercase for robust matching
    try:
        s = str(path.resolve())
    except Exception:
        s = str(path)
    return s.replace("\\", "/").lower()

def merge_dict(a: dict, b: dict) -> dict:
    out = dict(a or {})
    for k, v in (b or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = merge_dict(out[k], v)
        else:
            out[k] = v
    return out

# ---- Config handling ----
def load_config(path: str | None) -> dict:
    if not path:
        return {}
    p = Path(path)
    if not p.exists():
        print(f"[WARN] Config not found: {p} (continuing with defaults)", file=sys.stderr)
        return {}
    try:
        if p.suffix.lower() in (".yaml",".yml"):
            if yaml is None:
                raise RuntimeError("PyYAML not installed. Install with: pip install pyyaml")
            with open(p, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        else:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f) or {}
    except Exception as e:
        print(f"[ERROR] Failed to parse config {p}: {e}", file=sys.stderr)
        sys.exit(2)

def build_settings(cfg: dict, cli_args) -> dict:
    # Layer defaults <- config <- CLI
    settings = {
        "db": DEFAULT_DB,
        "excludes": set(DEFAULT_EXCLUDES),
        "exclude_globs": [],
        "auto_component_map": dict(DEFAULT_AUTO_COMPONENT_MAP),
        "path_component_rules": [],  # [{type: 'glob'|'regex', pattern: '...', component: '...'}]
        "category_by_ext": {},       # {".py": "code", ".json":"config"}
        "tag_static": [],            # ["project_huey", "prod"]
        "tag_by_ext": {},            # {".mq4": ["mql4","ea"]}
        "tag_by_folder": {},         # {"mt4_dde_interface": ["dde"]}
        "default_component": None,
        "max_hash_mb_default": None,
    }
    # merge config
    settings["db"] = cfg.get("db", settings["db"])
    settings["excludes"] |= set(cfg.get("exclude_dirs", []))
    settings["exclude_globs"] = cfg.get("exclude_globs", settings["exclude_globs"])
    settings["auto_component_map"] = merge_dict(settings["auto_component_map"], cfg.get("auto_component_map", {}))
    settings["path_component_rules"] = cfg.get("path_component_rules", settings["path_component_rules"])
    settings["category_by_ext"] = merge_dict(settings["category_by_ext"], cfg.get("category_by_ext", {}))
    settings["tag_static"] = cfg.get("tag_static", settings["tag_static"])
    settings["tag_by_ext"] = merge_dict(settings["tag_by_ext"], cfg.get("tag_by_ext", {}))
    settings["tag_by_folder"] = merge_dict(settings["tag_by_folder"], cfg.get("tag_by_folder", {}))
    settings["default_component"] = cfg.get("default_component", settings["default_component"])
    settings["max_hash_mb_default"] = cfg.get("max_hash_mb_default", settings["max_hash_mb_default"])

    # CLI wins
    if cli_args.db:
        settings["db"] = cli_args.db
    if cli_args.max_hash_mb is not None:
        settings["max_hash_bytes"] = cli_args.max_hash_mb * 1024 * 1024
    else:
        settings["max_hash_bytes"] = (settings["max_hash_mb_default"] or 0) * 1024 * 1024 if settings["max_hash_mb_default"] else None

    return settings

# ---- DB helpers ----
def file_category_id(cur, name):
    row = cur.execute("SELECT id FROM file_categories WHERE name=?;", (name,)).fetchone()
    if not row:
        cur.execute("INSERT INTO file_categories(name, description) VALUES (?, ?);", (name, f"Autocreated category: {name}"))
        return cur.lastrowid
    return row[0]

def component_id(cur, component_name):
    row = cur.execute("SELECT id FROM components WHERE name=?;", (component_name,)).fetchone()
    if row:
        return row[0]
    cur.execute("INSERT INTO components(name, type_id, description) VALUES (?,?,?);",
                (component_name, None, "Autocreated by repo ingester"))
    return cur.lastrowid

def ensure_directory(cur, dir_path: Path):
    # insert chain for parent_id linking
    parts = list(Path(dir_path).resolve().parts)
    running = Path(parts[0])
    last_id = None
    for part in parts[1:]:
        running = running / part
        row = cur.execute("SELECT id FROM directories WHERE path=?", (str(running),)).fetchone()
        if row:
            last_id = row[0]
        else:
            parent_row = cur.execute("SELECT id FROM directories WHERE path=?", (str(running.parent),)).fetchone()
            parent_id = parent_row[0] if parent_row else None
            cur.execute("INSERT INTO directories(path, parent_id) VALUES (?,?)", (str(running), parent_id))
            last_id = cur.lastrowid
    return last_id

def ensure_tag(cur, tag: str):
    row = cur.execute("SELECT id FROM tags WHERE tag=?;", (tag,)).fetchone()
    if row:
        return row[0]
    cur.execute("INSERT INTO tags(tag) VALUES (?);", (tag,))
    return cur.lastrowid

def set_file_tags(cur, file_id: int, tags: set):
    cur.execute("DELETE FROM file_tags WHERE file_id=?;", (file_id,))
    for t in sorted(tags):
        tid = ensure_tag(cur, t)
        cur.execute("INSERT OR IGNORE INTO file_tags(file_id, tag_id) VALUES (?,?);", (file_id, tid))

# ---- Classification / mapping ----
def is_excluded(path: Path, settings) -> bool:
    # exclude by dir name and by globs on normalized path
    parts = [p.lower() for p in path.parts]
    if any(part in settings["excludes"] for part in parts):
        return True
    norm = to_norm(path)
    for pat in settings["exclude_globs"]:
        if fnmatch.fnmatch(norm, pat.lower()):
            return True
    return False

def guess_category(p: Path, settings) -> str:
    ext = p.suffix.lower()
    if ext in settings["category_by_ext"]:
        return settings["category_by_ext"][ext]

    name = p.name.lower()
    parent_str = str(p.parent).lower()

    if ext == ".json" and ("schema" in name or name.endswith(".schema.json")):
        return "schema"
    if ext in {".json",".yaml",".yml",".ini",".cfg",".toml"}:
        return "config"
    if "tests" in parent_str or re.search(r"(?:^|[_-])test", name):
        return "test"
    if ext in {".ps1",".bat",".cmd",".sh"}:
        return "script"
    if ext in {".py",".mq4",".mqh",".cpp",".hpp",".h",".psm1"}:
        return "code"
    if ext in {".md",".rst",".adoc",".txt",".pdf"}:
        return "doc"
    if ext in {".csv",".db",".sqlite",".sqlite3",".parquet",".xlsx",".xls"}:
        return "data"
    if "logs" in parent_str or ext in {".log"}:
        return "log"
    if ext in {".dll",".exe",".pyd",".so",".dylib"}:
        return "binary"
    return "other"

def apply_path_component_rules(path: Path, settings):
    norm = to_norm(path)
    for rule in settings["path_component_rules"]:
        rtype = (rule.get("type") or "glob").lower()
        patt = rule.get("pattern", "")
        comp = rule.get("component")
        if not comp or not patt:
            continue
        if rtype == "glob":
            if fnmatch.fnmatch(norm, patt.lower()):
                return comp
        elif rtype == "regex":
            try:
                if re.search(patt, norm, flags=re.IGNORECASE):
                    return comp
            except re.error:
                pass
    return None

def auto_component_for_path(cur, path: Path, settings):
    # 1) explicit rules (glob/regex)
    comp = apply_path_component_rules(path, settings)
    if comp:
        return component_id(cur, comp)

    # 2) folder-keyword map
    for part in path.parts:
        key = part.lower()
        comp = settings["auto_component_map"].get(key)
        if comp:
            return component_id(cur, comp)

    # 3) default
    if settings["default_component"]:
        return component_id(cur, settings["default_component"])

    return None

def classify_tags(path: Path, comp_name: str | None, category: str, settings) -> set:
    tags = set(settings["tag_static"] or [])
    if comp_name:
        tags.add(comp_name.lower().replace(" ", "_"))
    tags.add(category)
    ext = path.suffix.lower()
    if ext:
        tags.add(ext.lstrip("."))
        for t in settings["tag_by_ext"].get(ext, []):
            tags.add(t)
    for part in path.parts:
        part_l = part.lower()
        if part_l in settings["auto_component_map"]:
            tags.add(part_l)
        for t in settings["tag_by_folder"].get(part_l, []):
            tags.add(t)
    return tags

# ---- Core ingest ----
def upsert_file(cur, full_path: Path, settings, description=None, verbose=False):
    try:
        st = full_path.stat()
    except Exception as e:
        if verbose:
            print(f"[WARN] Stat failed for {full_path}: {e}")
        return "error", None

    dir_id = ensure_directory(cur, full_path.parent)
    category = guess_category(full_path, settings)
    cat_id = file_category_id(cur, category)

    comp_id = auto_component_for_path(cur, full_path, settings)
    comp_name = None
    if comp_id:
        comp_name = cur.execute("SELECT name FROM components WHERE id=?;", (comp_id,)).fetchone()[0]

    mtime_iso = iso_utc(st.st_mtime)
    ctime_iso = iso_utc(st.st_ctime)
    size_bytes = st.st_size
    sha = sha256sum(full_path, max_bytes=settings.get("max_hash_bytes"))

    row = cur.execute("SELECT id, size_bytes, mtime_utc, sha256 FROM files WHERE path=?;", (str(full_path),)).fetchone()

    if row:
        fid, old_size, old_mtime, old_sha = row
        changed = (old_size != size_bytes) or (old_mtime != mtime_iso) or (old_sha != sha) or (comp_id is not None)
        if changed:
            cur.execute("""
                UPDATE files
                   SET directory_id=?, component_id=?, category_id=?, basename=?, ext=?,
                       size_bytes=?, sha256=?, mtime_utc=?, ctime_utc=?, description=COALESCE(?,description), is_active=1
                 WHERE id=?;
            """, (dir_id, comp_id, cat_id, full_path.name, full_path.suffix, size_bytes, sha, mtime_iso, ctime_iso, description, fid))
            status = "updated"
        else:
            status = "skipped"
        set_file_tags(cur, fid, classify_tags(full_path, comp_name, category, settings))
        return status, fid
    else:
        cur.execute("""
            INSERT INTO files(directory_id, component_id, category_id, path, basename, ext,
                              size_bytes, sha256, mtime_utc, ctime_utc, description, is_active)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,1);
        """, (dir_id, comp_id, cat_id, str(full_path), full_path.name, full_path.suffix, size_bytes, sha, mtime_iso, ctime_iso, description))
        fid = cur.lastrowid
        set_file_tags(cur, fid, classify_tags(full_path, comp_name, category, settings))
        return "inserted", fid

def walk_and_ingest(root: Path, settings, verbose=False, dry_run=False):
    db_path = settings["db"]
    if not Path(db_path).exists():
        print(f"[ERROR] DB not found at: {db_path}", file=sys.stderr)
        sys.exit(2)

    con = sqlite3.connect(db_path)
    con.execute("PRAGMA foreign_keys=ON;")
    cur = con.cursor()

    inserted = updated = skipped = errors = 0
    root = root.resolve()

    for p in root.rglob("*"):
        if p.is_dir():
            if is_excluded(p, settings):
                if verbose:
                    print(f"[SKIP] dir: {p}")
                continue
            continue
        if is_excluded(p, settings):
            if verbose:
                print(f"[SKIP] file: {p}")
            continue
        try:
            status, fid = upsert_file(cur, p, settings, verbose=verbose)
            if status == "inserted": inserted += 1
            elif status == "updated": updated += 1
            elif status == "skipped": skipped += 1
            else: errors += 1
        except KeyboardInterrupt:
            print("\n[ABORT] Interrupted by user.")
            break
        except Exception as e:
            errors += 1
            if verbose:
                print(f"[ERROR] {p}: {e}")

    if dry_run:
        con.rollback()
        print(f"[DRY-RUN] inserted={inserted}, updated={updated}, skipped={skipped}, errors={errors}")
    else:
        con.commit()
        print(f"[OK] inserted={inserted}, updated={updated}, skipped={skipped}, errors={errors}")

    con.close()

def main():
    ap = argparse.ArgumentParser(description="Repo ingester: walk, hash, classify, tag, auto-map to components, push to SQLite. Supports JSON/YAML config.")
    ap.add_argument("root", help="Path to repository root (e.g., C:\\Projects\\HUEY_P or .)")
    ap.add_argument("--db", default=None, help="Path to SQLite DB (overrides config/default)")
    ap.add_argument("--config", help="Path to JSON or YAML config file")
    ap.add_argument("--max-hash-mb", type=int, default=None, help="Limit hashing to first N MB (overrides config)")
    ap.add_argument("--verbose", "-v", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cfg = load_config(args.config)
    settings = build_settings(cfg, args)

    root = Path(args.root)
    if not root.exists():
        print(f"[ERROR] Root folder does not exist: {root}", file=sys.stderr)
        sys.exit(2)

    walk_and_ingest(root, settings, verbose=args.verbose, dry_run=args.dry_run)

if __name__ == "__main__":
    main()
