-- Applied at: 2025-08-23T05:32:17Z UTC

-- === Recommended Indexes ===
CREATE INDEX IF NOT EXISTS idx_files_mtime ON files(mtime_utc);
CREATE INDEX IF NOT EXISTS idx_files_component ON files(component_id);
CREATE INDEX IF NOT EXISTS idx_files_category ON files(category_id);
CREATE INDEX IF NOT EXISTS idx_files_directory ON files(directory_id);
CREATE INDEX IF NOT EXISTS idx_files_component_mtime ON files(component_id, mtime_utc);

CREATE INDEX IF NOT EXISTS idx_runs_started_at ON runs(started_at_utc);
CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status);
CREATE INDEX IF NOT EXISTS idx_runs_comp_param_time ON runs(component_id, parameter_set_id, started_at_utc);

CREATE INDEX IF NOT EXISTS idx_results_run ON results(run_id);
CREATE INDEX IF NOT EXISTS idx_results_metric ON results(metric);

CREATE INDEX IF NOT EXISTS idx_param_sets_name ON parameter_sets(name);
CREATE INDEX IF NOT EXISTS idx_param_sets_created ON parameter_sets(created_at_utc);
CREATE INDEX IF NOT EXISTS idx_param_values_set_key ON parameter_values(parameter_set_id, key);

CREATE INDEX IF NOT EXISTS idx_combo_param_hash ON combination_ids(parameter_set_id, combo_hash);

CREATE INDEX IF NOT EXISTS idx_signals_type ON signals(type_id);
CREATE INDEX IF NOT EXISTS idx_signals_source_file ON signals(source_file_id);

CREATE INDEX IF NOT EXISTS idx_comm_protocol ON communications(protocol_id);
CREATE INDEX IF NOT EXISTS idx_comm_layer ON communications(layer);
CREATE INDEX IF NOT EXISTS idx_comm_port ON communications(port);

CREATE INDEX IF NOT EXISTS idx_dirs_parent ON directories(parent_id);
CREATE INDEX IF NOT EXISTS idx_file_tags_file ON file_tags(file_id);
CREATE INDEX IF NOT EXISTS idx_file_tags_tag ON file_tags(tag_id);

CREATE INDEX IF NOT EXISTS idx_questions_status ON questions(status);
CREATE INDEX IF NOT EXISTS idx_questions_topic ON questions(topic);

-- JSON helper indexes (requires JSON1; safe if column is NULL)
CREATE INDEX IF NOT EXISTS idx_signals_cfg_timeframe ON signals(json_extract(config_json, '$.timeframe'));
CREATE INDEX IF NOT EXISTS idx_signals_cfg_indicator ON signals(json_extract(config_json, '$.indicator'));

-- === JSON Validation Triggers ===
DROP TRIGGER IF EXISTS trg_calendar_filters_validate_json_ins;
DROP TRIGGER IF EXISTS trg_calendar_filters_validate_json_upd;
CREATE TRIGGER trg_calendar_filters_validate_json_ins
BEFORE INSERT ON calendar_filters
WHEN NEW.rules_json IS NOT NULL AND NOT json_valid(NEW.rules_json)
BEGIN
  SELECT RAISE(ABORT, 'calendar_filters.rules_json must be valid JSON');
END;
CREATE TRIGGER trg_calendar_filters_validate_json_upd
BEFORE UPDATE ON calendar_filters
WHEN NEW.rules_json IS NOT NULL AND NOT json_valid(NEW.rules_json)
BEGIN
  SELECT RAISE(ABORT, 'calendar_filters.rules_json must be valid JSON');
END;

DROP TRIGGER IF EXISTS trg_signals_validate_json_ins;
DROP TRIGGER IF EXISTS trg_signals_validate_json_upd;
CREATE TRIGGER trg_signals_validate_json_ins
BEFORE INSERT ON signals
WHEN NEW.config_json IS NOT NULL AND NOT json_valid(NEW.config_json)
BEGIN
  SELECT RAISE(ABORT, 'signals.config_json must be valid JSON');
END;
CREATE TRIGGER trg_signals_validate_json_upd
BEFORE UPDATE ON signals
WHEN NEW.config_json IS NOT NULL AND NOT json_valid(NEW.config_json)
BEGIN
  SELECT RAISE(ABORT, 'signals.config_json must be valid JSON');
END;

-- === FTS5 Sync Triggers (contentless external table) ===
-- Files
DROP TRIGGER IF EXISTS trg_files_ai_fts;
DROP TRIGGER IF EXISTS trg_files_au_fts;
DROP TRIGGER IF EXISTS trg_files_ad_fts;
CREATE TRIGGER trg_files_ai_fts AFTER INSERT ON files BEGIN
  INSERT INTO fts_files(rowid, path, basename, ext, description, tags)
  SELECT NEW.id, NEW.path, NEW.basename, NEW.ext, COALESCE(NEW.description,''),
         (SELECT group_concat(t.tag, ' ')
            FROM file_tags ft JOIN tags t ON ft.tag_id=t.id
           WHERE ft.file_id=NEW.id);
END;
CREATE TRIGGER trg_files_au_fts AFTER UPDATE ON files BEGIN
  DELETE FROM fts_files WHERE rowid=OLD.id;
  INSERT INTO fts_files(rowid, path, basename, ext, description, tags)
  SELECT NEW.id, NEW.path, NEW.basename, NEW.ext, COALESCE(NEW.description,''),
         (SELECT group_concat(t.tag, ' ')
            FROM file_tags ft JOIN tags t ON ft.tag_id=t.id
           WHERE ft.file_id=NEW.id);
END;
CREATE TRIGGER trg_files_ad_fts AFTER DELETE ON files BEGIN
  DELETE FROM fts_files WHERE rowid=OLD.id;
END;

-- File tag changes
DROP TRIGGER IF EXISTS trg_file_tags_ai_fts;
DROP TRIGGER IF EXISTS trg_file_tags_ad_fts;
CREATE TRIGGER trg_file_tags_ai_fts AFTER INSERT ON file_tags BEGIN
  DELETE FROM fts_files WHERE rowid=NEW.file_id;
  INSERT INTO fts_files(rowid, path, basename, ext, description, tags)
  SELECT f.id, f.path, f.basename, f.ext, COALESCE(f.description,''),
         (SELECT group_concat(t.tag, ' ')
            FROM file_tags ft JOIN tags t ON ft.tag_id=t.id
           WHERE ft.file_id=f.id)
  FROM files f WHERE f.id=NEW.file_id;
END;
CREATE TRIGGER trg_file_tags_ad_fts AFTER DELETE ON file_tags BEGIN
  DELETE FROM fts_files WHERE rowid=OLD.file_id;
  INSERT INTO fts_files(rowid, path, basename, ext, description, tags)
  SELECT f.id, f.path, f.basename, f.ext, COALESCE(f.description,''),
         (SELECT group_concat(t.tag, ' ')
            FROM file_tags ft JOIN tags t ON ft.tag_id=t.id
           WHERE ft.file_id=f.id)
  FROM files f WHERE f.id=OLD.file_id;
END;

-- Tag text updates (rare)
DROP TRIGGER IF EXISTS trg_tags_au_fts;
CREATE TRIGGER trg_tags_au_fts AFTER UPDATE ON tags BEGIN
  -- Rebuild FTS rows for all files that use this tag
  DELETE FROM fts_files WHERE rowid IN (
    SELECT ft.file_id FROM file_tags ft WHERE ft.tag_id=NEW.id
  );
  INSERT INTO fts_files(rowid, path, basename, ext, description, tags)
  SELECT f.id, f.path, f.basename, f.ext, COALESCE(f.description,''),
         (SELECT group_concat(t.tag, ' ')
            FROM file_tags ft2 JOIN tags t ON ft2.tag_id=t.id
           WHERE ft2.file_id=f.id)
  FROM files f
  WHERE f.id IN (SELECT ft.file_id FROM file_tags ft WHERE ft.tag_id=NEW.id);
END;

-- === FTS maintenance helpers ===
-- To run:  INSERT INTO fts_files(fts_files) VALUES('optimize');
--          INSERT INTO fts_files(fts_files) VALUES('rebuild');
--          INSERT INTO fts_files(fts_files, rank) VALUES('merge', 32);
