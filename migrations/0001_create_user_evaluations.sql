CREATE TABLE IF NOT EXISTS user_evaluations (
    run_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    payload TEXT NOT NULL,
    starred INTEGER NOT NULL DEFAULT 0,
    deleted_at TEXT
);
