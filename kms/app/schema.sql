-- KMS control plane — minimal schema
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  path TEXT NOT NULL UNIQUE,
  kind TEXT NOT NULL DEFAULT 'file',
  hash TEXT,
  source_url TEXT,
  status TEXT NOT NULL DEFAULT 'new',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS proposals (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  item_id INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
  suggested_action TEXT NOT NULL,
  suggested_target TEXT,
  suggested_metadata_json TEXT,
  reason TEXT,
  created_at TEXT NOT NULL,
  lifecycle_status TEXT
);

CREATE INDEX IF NOT EXISTS idx_proposals_item ON proposals(item_id);

CREATE TABLE IF NOT EXISTS decisions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  proposal_id INTEGER NOT NULL UNIQUE REFERENCES proposals(id) ON DELETE CASCADE,
  decision TEXT NOT NULL DEFAULT 'pending',
  override_target TEXT,
  reviewer TEXT,
  review_note TEXT,
  decided_at TEXT
);

CREATE TABLE IF NOT EXISTS artifacts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  proposal_id INTEGER NOT NULL UNIQUE REFERENCES proposals(id) ON DELETE CASCADE,
  item_id INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
  source_note_path TEXT,
  workspace_name TEXT,
  -- AnythingLLM document ``location`` from upload response; used for update-embeddings deletes on revert.
  anythingllm_doc_location TEXT,
  applied_at TEXT NOT NULL,
  index_status TEXT NOT NULL DEFAULT 'pending'
);

-- One execution row per applied proposal: snapshot for revert + reverted_at when undone.
CREATE TABLE IF NOT EXISTS executions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  proposal_id INTEGER NOT NULL UNIQUE REFERENCES proposals(id) ON DELETE CASCADE,
  applied_at TEXT NOT NULL,
  reverted_at TEXT,
  snapshot_json TEXT NOT NULL,
  result_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_executions_proposal ON executions(proposal_id);

CREATE INDEX IF NOT EXISTS idx_artifacts_item ON artifacts(item_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_proposal ON artifacts(proposal_id);

CREATE TABLE IF NOT EXISTS audit_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  action TEXT NOT NULL,
  entity_type TEXT,
  entity_id TEXT,
  payload_json TEXT,
  error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_audit_ts ON audit_log(ts);
