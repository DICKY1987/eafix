Based on the system documentation, the matrix database is stored in multiple locations with a flexible, extensible structure:

## **Storage Locations**

### **Primary Database: SQLite/PostgreSQL**
- **Per-symbol tables** (e.g., `trades_EURUSD`, `reentry_chains_EURUSD`)
- **Core matrix tables:**
  - `combinations` - All possible combination IDs and dimensions
  - `responses` - Decision parameters for each combination
  - `cells` - Action configurations and performance metrics
  - `reentry_executions_<SYMBOL>` - Execution audit trail
  - `reentry_performance_<SYMBOL>` - KPI tracking

### **Configuration Files**
- **JSON matrices:** `current_matrix.json`, `matrix_{symbol}_v{timestamp}.json`
- **CSV profiles:** `<SYMBOL>_reentry.csv` (parameter sets 1-6)
- **YAML blueprints:** `reentry_blueprint.yaml` (rule definitions)

## **Extensibility Features**

### **Variable Modification Support**
**✅ Easy to Add Variables:**
- Schema uses TEXT fields for dimensions (`signal_type`, `time_category`, `context`)
- Combination IDs are string-based: `SYMBOL:SIGNAL:DURATION:O{outcome}:F{future}:P{past}:G{generation}`
- New dimensions can be added without breaking existing combinations

**✅ Easy to Remove Variables:**
- Normalized schema with foreign key cascades
- `version_tag` field allows deprecating old combinations
- JSON file versioning preserves historical configurations

**✅ Easy to Modify Variables:**
- `enabled` boolean flag for temporarily disabling combinations
- `updated_at` timestamps track changes
- Atomic file replacement prevents corruption during updates

### **Flexible Schema Design**
```sql
-- Combinations table supports any dimension set
CREATE TABLE combinations(
  symbol TEXT,
  signal_type TEXT,        -- Extensible: add new signal types
  time_category TEXT,      -- Extensible: modify time buckets  
  outcome INTEGER,         -- Fixed: 1-6 buckets
  context TEXT,           -- Extensible: proximity/market context
  generation INTEGER,      -- Fixed: 0-2 for original/reentries
  combination_id TEXT UNIQUE,
  created_at TEXT,
  updated_at TEXT
);

-- Responses table decoupled from dimensions
CREATE TABLE responses(
  combination_id TEXT PRIMARY KEY,
  decision TEXT,           -- REENTRY | END_TRADING
  size_multiplier REAL,
  confidence_adjustment REAL,
  delay_minutes INTEGER,
  enabled BOOLEAN,
  version_tag TEXT,
  notes TEXT
);
```

### **Migration Support**
- **Automated migration script:** `sqlite_reentry_migrate.py`
- **Idempotent operations:** Safe to run multiple times
- **Column addition:** `ALTER TABLE` statements for new fields
- **Index management:** Automatic performance optimization

### **Configuration Management**
- **Profile deployment:** PowerShell scripts for persona switching
- **Live reload:** Runtime configuration updates without EA restart
- **Version control:** Timestamped backups of all configuration changes

The system is specifically designed for experimentation and optimization, making it straightforward to add new signal types, modify time categorizations, or introduce additional decision variables without disrupting existing functionality.