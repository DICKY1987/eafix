#!/usr/bin/env python3

import argparse, os, sqlite3, hashlib, json, re, sys, time, datetime as dt
from pathlib import Path

EXCLUDES = {'.git', '__pycache__', '.venv', 'node_modules', '.idea', '.vscode', 'dist', 'build', '.mypy_cache', '.ruff_cache'}

DEFAULT_DB = r"/mnt/data/huey_project_organizer.db"  # override with --db on Windows
CHUNK = 1024 * 1024

# Heuristic folder->component mapping (lowercase match against any path part)
AUTO_COMPONENT_MAP = {
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

def sha256sum(path, max_bytes=None):
    h = hashlib.sha256()
    read = 0
    with open(path, "rb") as f:
        while True:
            chunk = f.read(CHUNK)
            if not chunk:
                break
            h.update(chunk)
            read += len(chunk)
            if max_bytes and read >= max_bytes:
                break
    return h.hexdigest()

def iso_utc(ts):
    return dt.datetime.utcfromtimestamp(ts).strftime("%Y-%m-%dT%H:%M:%SZ")

def should_exclude(path: Path):
    for part in path.parts:
        if part in EXCLUDES:
            return True
    return False

def guess_category(p: Path):
    name = p.name.lower()
    ext = p.suffix.lower()
    parent_str = str(p.parent).lower()

    # schema first (e.g., *.schema.json or file with 'schema' in name)
    if ext == ".json" and ("schema" in name or name.endswith(".schema.json")):
        return "schema"

    # config
    if ext in {".json",".yaml",".yml",".ini",".cfg",".toml"}:
        return "config"

    # tests
    if "tests" in parent_str or re.search(r"(?:^|[_-])test", name):
        return "test"

    # scripts
    if ext in {".ps1",".bat",".cmd",".sh"}:
        return "script"

    # code
    if ext in {".py",".mq4",".mqh",".cpp",".hpp",".h",".psm1"}:
        return "code"

    # docs
    if ext in {".md",".rst",".adoc",".txt",".pdf"}:
        return "doc"

    # data
    if ext in {".csv",".db",".sqlite",".sqlite3",".parquet",".xlsx",".xls"}:
        return "data"

    # logs
    if "logs" in parent_str or ext in {".log"}:
        return "log"

    # binaries
    if ext in {".dll",".exe",".pyd",".so",".dylib"}:
        return "binary"

    return "other"

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
    # fallback: try to create a new generic component under a guessed type if unknown
    cur.execute("INSERT INTO components(name, type_id, description) VALUES (?, ?, ?);",
                (component_name, None, "Autocreated by repo ingester"))
    return cur.lastrowid

def auto_component_for_path(cur, path: Path):
    parts = [p.lower() for p in path.parts]
    for part in parts:
        comp = AUTO_COMPONENT_MAP.get(part)
        if comp:
            return component_id(cur, comp)
    return None

def ensure_directory(cur, dir_path: Path):
    # Insert chain of directories so parent_id links are valid
    # Store normalized (Windows or POSIX) absolute path as string
    def upsert(path: Path):
        parent = str(path.parent)
        parent_id = None
        if parent and parent != str(path):
            parent_id = cur.execute("SELECT id FROM directories WHERE path=?", (parent,)).fetchone()
            parent_id = parent_id[0] if parent_id else None
        row = cur.execute("SELECT id FROM directories WHERE path=?", (str(path),)).fetchone()
        if row:
            return row[0]
        cur.execute("INSERT INTO directories(path, parent_id) VALUES (?,?)", (str(path), parent_id))
        return cur.lastrowid

    # build from root down
    parts = list(Path(dir_path).resolve().parts)
    running = Path(parts[0])
    ensure_id = None
    for part in parts[1:]:
        running = running / part
        ensure_id = upsert(running)
    return ensure_id

def ensure_tag(cur, tag: str):
    row = cur.execute("SELECT id FROM tags WHERE tag=?;", (tag,)).fetchone()
    if row:
        return row[0]
    cur.execute("INSERT INTO tags(tag) VALUES (?);", (tag,))
    return cur.lastrowid

def set_file_tags(cur, file_id: int, tags: set):
    # Remove existing then re-add to reflect new classification
    cur.execute("DELETE FROM file_tags WHERE file_id=?;", (file_id,))
    for t in sorted(tags):
        tid = ensure_tag(cur, t)
        cur.execute("INSERT OR IGNORE INTO file_tags(file_id, tag_id) VALUES (?,?);", (file_id, tid))

def classify_tags(path: Path, comp_name: str | None, category: str):
    tags = set()
    if comp_name:
        tags.add(comp_name.lower().replace(" ", "_"))
    tags.add(category)
    # extension tag
    ext = path.suffix.lower()
    if ext:
        tags.add(ext.lstrip("."))
    # folder hints
    for part in path.parts:
        part_l = part.lower()
        if part_l in AUTO_COMPONENT_MAP:
            tags.add(part_l)
    return tags

def upsert_file(cur, full_path: Path, max_hash_bytes=None, component_override=None, description=None, verbose=False):
    try:
        st = full_path.stat()
    except Exception as e:
        if verbose:
            print(f"[WARN] Stat failed for {full_path}: {e}")
        return "error", None

    dir_id = ensure_directory(cur, full_path.parent)
    category = guess_category(full_path)
    cat_id = file_category_id(cur, category)

    comp_id = component_override or auto_component_for_path(cur, full_path)
    comp_name = None
    if comp_id:
        comp_name = cur.execute("SELECT name FROM components WHERE id=?;", (comp_id,)).fetchone()[0]

    mtime_iso = iso_utc(st.st_mtime)
    ctime_iso = iso_utc(st.st_ctime)
    size_bytes = st.st_size
    sha = sha256sum(full_path, max_hash_bytes=max_hash_bytes)

    row = cur.execute("SELECT id, size_bytes, mtime_utc, sha256 FROM files WHERE path=?;", (str(full_path),)).fetchone()

    if row:
        fid, old_size, old_mtime, old_sha = row
        changed = (old_size != size_bytes) or (old_mtime != mtime_iso) or (old_sha != sha) or (component_override is not None)
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
        set_file_tags(cur, fid, classify_tags(full_path, comp_name, category))
        return status, fid
    else:
        cur.execute("""
            INSERT INTO files(directory_id, component_id, category_id, path, basename, ext,
                              size_bytes, sha256, mtime_utc, ctime_utc, description, is_active)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,1);
        """, (dir_id, comp_id, cat_id, str(full_path), full_path.name, full_path.suffix, size_bytes, sha, mtime_iso, ctime_iso, description))
        fid = cur.lastrowid
        set_file_tags(cur, fid, classify_tags(full_path, comp_name, category))
        return "inserted", fid

def walk_and_ingest(root: Path, db_path: str, max_hash_bytes=None, verbose=False, dry_run=False):
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
            if should_exclude(p):
                if verbose:
                    print(f"[SKIP] dir: {p}")
                # skip walking into excluded dir by clearing its iterator via continue; rglob already descended
                continue
            continue
        if should_exclude(p):
            if verbose:
                print(f"[SKIP] file: {p}")
            continue
        try:
            status, fid = upsert_file(cur, p, max_hash_bytes=max_hash_bytes, verbose=verbose)
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
    ap = argparse.ArgumentParser(description="Windows-friendly repo ingester: walk, hash, classify, tag, and push files into the SQLite organizer DB.")
    ap.add_argument("root", help="Path to the repository root (e.g., C:\\Projects\\HUEY_P or .)")
    ap.add_argument("--db", default=DEFAULT_DB, help="Path to the SQLite DB (default: %(default)s)")
    ap.add_argument("--max-hash-mb", type=int, default=None, help="Limit hashing to first N MB for speed (omit to hash full file)")
    ap.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    ap.add_argument("--dry-run", action="store_true", help="Do not commit; just report")
    args = ap.parse_args()

    root = Path(args.root)
    if not root.exists():
        print(f"[ERROR] Root folder does not exist: {root}", file=sys.stderr)
        sys.exit(2)

    max_bytes = args.max_hash_mb * 1024 * 1024 if args.max_hash_mb else None
    walk_and_ingest(root, args.db, max_hash_bytes=max_bytes, verbose=args.verbose, dry_run=args.dry_run)

if __name__ == "__main__":
    main()
