CREATE TABLE calendar_filters(
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT,
  rules_json TEXT  -- stores scoring system, sources, exclusion rules, etc.
);
CREATE TABLE combination_ids(
  id INTEGER PRIMARY KEY,
  parameter_set_id INTEGER REFERENCES parameter_sets(id) ON DELETE SET NULL,
  combo_key TEXT NOT NULL,
  combo_hash TEXT UNIQUE,
  description TEXT
);
CREATE TABLE communications(
  id INTEGER PRIMARY KEY,
  layer TEXT,   -- Python, MT4, DLL, CSV, DDE
  protocol_id INTEGER REFERENCES protocol_types(id),
  direction TEXT CHECK(direction IN ('inbound','outbound','bidirectional')),
  host TEXT,
  port INTEGER,
  path TEXT,
  notes TEXT
);
CREATE TABLE component_types(
  id INTEGER PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  description TEXT
);
CREATE TABLE components(
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  type_id INTEGER REFERENCES component_types(id),
  description TEXT
);
CREATE TABLE directories(
  id INTEGER PRIMARY KEY,
  path TEXT UNIQUE NOT NULL,
  parent_id INTEGER REFERENCES directories(id)
);
CREATE TABLE file_categories(
  id INTEGER PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  description TEXT
);
CREATE TABLE file_tags(
  file_id INTEGER REFERENCES files(id) ON DELETE CASCADE,
  tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
  PRIMARY KEY(file_id, tag_id)
);
CREATE TABLE files(
  id INTEGER PRIMARY KEY,
  directory_id INTEGER REFERENCES directories(id),
  component_id INTEGER REFERENCES components(id),
  category_id INTEGER REFERENCES file_categories(id),
  path TEXT UNIQUE NOT NULL,
  basename TEXT NOT NULL,
  ext TEXT,
  size_bytes INTEGER,
  sha256 TEXT,
  mtime_utc TEXT,
  ctime_utc TEXT,
  description TEXT,
  is_active INTEGER DEFAULT 1
);
CREATE VIRTUAL TABLE fts_files USING fts5(
  path, basename, ext, description, tags, content=''
);
CREATE TABLE 'fts_files_config'(k PRIMARY KEY, v) WITHOUT ROWID;
CREATE TABLE 'fts_files_data'(id INTEGER PRIMARY KEY, block BLOB);
CREATE TABLE 'fts_files_docsize'(id INTEGER PRIMARY KEY, sz BLOB);
CREATE TABLE 'fts_files_idx'(segid, term, pgno, PRIMARY KEY(segid, term)) WITHOUT ROWID;
CREATE TABLE glossary(
  id INTEGER PRIMARY KEY,
  term TEXT UNIQUE NOT NULL,
  definition TEXT,
  category TEXT
);
CREATE TABLE impact_levels(
  id INTEGER PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  description TEXT
);
CREATE TABLE meta(
  key TEXT PRIMARY KEY,
  value TEXT
);
CREATE TABLE parameter_sets(
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  source TEXT CHECK(source IN ('csv','json','yaml','ui','other')),
  version TEXT,
  created_at_utc TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
  notes TEXT
);
CREATE TABLE parameter_values(
  id INTEGER PRIMARY KEY,
  parameter_set_id INTEGER REFERENCES parameter_sets(id) ON DELETE CASCADE,
  key TEXT NOT NULL,
  value TEXT,
  dtype TEXT CHECK(dtype IN ('int','float','str','bool','json','other'))
);
CREATE TABLE protocol_types(
  id INTEGER PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  description TEXT
);
CREATE TABLE questions(
  id INTEGER PRIMARY KEY,
  topic TEXT NOT NULL,
  question TEXT NOT NULL,
  status TEXT CHECK(status IN ('open','answered','deferred')) DEFAULT 'open',
  notes TEXT
);
CREATE TABLE relationships(
  id INTEGER PRIMARY KEY,
  from_type TEXT NOT NULL CHECK(from_type IN ('file','component','parameter_set','signal','run','calendar_filter')),
  from_id INTEGER NOT NULL,
  to_type TEXT NOT NULL CHECK(to_type IN ('file','component','parameter_set','signal','run','calendar_filter')),
  to_id INTEGER NOT NULL,
  relation TEXT NOT NULL  -- e.g., 'depends_on','produces','consumes','config_of'
);
CREATE TABLE results(
  id INTEGER PRIMARY KEY,
  run_id INTEGER REFERENCES runs(id) ON DELETE CASCADE,
  metric TEXT NOT NULL,
  value REAL,
  unit TEXT,
  extra_json TEXT
);
CREATE TABLE runs(
  id INTEGER PRIMARY KEY,
  started_at_utc TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
  ended_at_utc TEXT,
  symbol TEXT,
  timeframe TEXT,
  component_id INTEGER REFERENCES components(id),
  parameter_set_id INTEGER REFERENCES parameter_sets(id),
  status TEXT CHECK(status IN ('planned','running','success','failed','aborted')) DEFAULT 'planned',
  notes TEXT
);
CREATE TABLE signal_types(
  id INTEGER PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  description TEXT
);
CREATE TABLE signals(
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  type_id INTEGER REFERENCES signal_types(id),
  indicator TEXT,
  timeframe TEXT,
  source_file_id INTEGER REFERENCES files(id),
  config_json TEXT
);
CREATE TABLE tags(
  id INTEGER PRIMARY KEY,
  tag TEXT UNIQUE NOT NULL
);
CREATE VIEW vw_files_by_component AS
SELECT c.name AS component, f.path, f.basename, f.ext, f.description
FROM files f LEFT JOIN components c ON f.component_id=c.id
ORDER BY c.name, f.basename;
CREATE VIEW vw_recent_files AS
SELECT path, basename, mtime_utc FROM files ORDER BY mtime_utc DESC;
CREATE VIEW vw_unassigned_files AS
SELECT path, basename, ext, description FROM files WHERE component_id IS NULL;
