-- ============================================================
-- QUIZZONE D1 — Schema v2
-- Deploy: wrangler d1 execute quizzone --file=db/schema.sql
-- ============================================================

CREATE TABLE IF NOT EXISTS games (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  upload_id TEXT UNIQUE NOT NULL,
  quiz_id TEXT NOT NULL,
  quiz_title TEXT,
  player_key TEXT,
  player_name_raw TEXT NOT NULL,
  timestamp TEXT NOT NULL,
  score INTEGER NOT NULL DEFAULT 0,
  correct INTEGER NOT NULL DEFAULT 0,
  total INTEGER NOT NULL DEFAULT 0,
  percentage INTEGER NOT NULL DEFAULT 0,
  max_streak INTEGER DEFAULT 0,
  avg_time REAL DEFAULT 0,
  multiplier_used INTEGER DEFAULT 0,
  multiplier_remaining INTEGER DEFAULT 0,
  source TEXT NOT NULL DEFAULT 'upload',
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS answers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
  question_num INTEGER NOT NULL,
  question_text TEXT,
  category TEXT,
  is_correct INTEGER NOT NULL DEFAULT 0,
  is_timeout INTEGER NOT NULL DEFAULT 0,
  points INTEGER DEFAULT 0,
  streak_bonus INTEGER DEFAULT 0,
  multiplier_used INTEGER DEFAULT 0,
  time_used REAL DEFAULT 0,
  chosen_option TEXT,
  correct_option TEXT,
  contest TEXT DEFAULT NULL,
  UNIQUE(game_id, question_num)
);

CREATE INDEX IF NOT EXISTS idx_games_player ON games(player_key);
CREATE INDEX IF NOT EXISTS idx_games_quiz ON games(quiz_id);
CREATE INDEX IF NOT EXISTS idx_answers_game ON answers(game_id);
CREATE INDEX IF NOT EXISTS idx_answers_contest ON answers(contest) WHERE contest IS NOT NULL;
