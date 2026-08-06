"""Базовые функции для работы с БД."""
import os
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_FILE = os.path.join(BASE_DIR, "game.db")


def get_conn():
    """Получить подключение к БД."""
    conn = sqlite3.connect(DB_FILE, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=10000")
    return conn


def add_column_if_not_exists(conn, table, column, definition):
    """Добавить колонку если её нет."""
    try:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
    except sqlite3.OperationalError:
        pass


def init_db():
    """Инициализировать все таблицы."""
    conn = get_conn()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS players (
                user_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                balance INTEGER NOT NULL DEFAULT 100,
                level INTEGER NOT NULL DEFAULT 1,
                exp INTEGER NOT NULL DEFAULT 0,
                last_work INTEGER NOT NULL DEFAULT 0,
                last_bonus TEXT NOT NULL DEFAULT '',
                bonus_streak INTEGER NOT NULL DEFAULT 0,
                last_peer_id INTEGER,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER NOT NULL,
                item_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (player_id) REFERENCES players(user_id) ON DELETE CASCADE,
                UNIQUE(player_id, item_id)
            );
            CREATE TABLE IF NOT EXISTS equipment (
                player_id INTEGER PRIMARY KEY,
                weapon INTEGER,
                armor INTEGER,
                cosmetic INTEGER,
                FOREIGN KEY (player_id) REFERENCES players(user_id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS pets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER NOT NULL,
                pet_id INTEGER NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 0,
                acquired_at TEXT NOT NULL,
                FOREIGN KEY (player_id) REFERENCES players(user_id) ON DELETE CASCADE,
                UNIQUE(player_id, pet_id)
            );
            CREATE TABLE IF NOT EXISTS duels (
                challenged_id INTEGER PRIMARY KEY,
                challenger_id INTEGER NOT NULL,
                challenger_peer_id INTEGER NOT NULL,
                timestamp REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS boss (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                active INTEGER NOT NULL DEFAULT 0,
                level INTEGER NOT NULL DEFAULT 1,
                name TEXT NOT NULL DEFAULT '',
                max_hp INTEGER NOT NULL DEFAULT 0,
                current_hp INTEGER NOT NULL DEFAULT 0,
                attack INTEGER NOT NULL DEFAULT 0,
                defense INTEGER NOT NULL DEFAULT 0,
                start_time REAL
            );
            CREATE TABLE IF NOT EXISTS boss_participants (
                boss_id INTEGER NOT NULL,
                player_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                damage INTEGER NOT NULL DEFAULT 0,
                peer_id INTEGER NOT NULL,
                PRIMARY KEY (boss_id, player_id),
                FOREIGN KEY (boss_id) REFERENCES boss(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS achievements (
                user_id INTEGER NOT NULL,
                achievement_id TEXT NOT NULL,
                unlocked_at TEXT NOT NULL,
                PRIMARY KEY (user_id, achievement_id),
                FOREIGN KEY (user_id) REFERENCES players(user_id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS seasons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                season_number INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                position INTEGER NOT NULL,
                season_points INTEGER NOT NULL,
                reward_coins INTEGER NOT NULL,
                title TEXT NOT NULL,
                ended_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES players(user_id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS clans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                leader_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                level INTEGER NOT NULL DEFAULT 1,
                exp INTEGER NOT NULL DEFAULT 0,
                coins INTEGER NOT NULL DEFAULT 0,
                wins INTEGER NOT NULL DEFAULT 0,
                losses INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (leader_id) REFERENCES players(user_id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS clan_members (
                clan_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL DEFAULT 'member',
                joined_at TEXT NOT NULL,
                PRIMARY KEY (clan_id, user_id),
                FOREIGN KEY (clan_id) REFERENCES clans(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES players(user_id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS clan_wars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                clan1_id INTEGER NOT NULL,
                clan2_id INTEGER NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT,
                winner_id INTEGER,
                clan1_score INTEGER DEFAULT 0,
                clan2_score INTEGER DEFAULT 0,
                FOREIGN KEY (clan1_id) REFERENCES clans(id) ON DELETE CASCADE,
                FOREIGN KEY (clan2_id) REFERENCES clans(id) ON DELETE CASCADE
            );
            
            -- PvP вызовы (новая таблица)
            CREATE TABLE IF NOT EXISTS duel_challenges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                challenger_id INTEGER NOT NULL,
                target_id INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );
            
            -- Активные дуэли (новая таблица)
            CREATE TABLE IF NOT EXISTS active_duels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player1_id INTEGER NOT NULL,
                player2_id INTEGER NOT NULL,
                stake INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                winner_id INTEGER,
                created_at TEXT NOT NULL,
                finished_at TEXT
            );
            
            CREATE INDEX IF NOT EXISTS idx_inventory_player ON inventory(player_id);
            CREATE INDEX IF NOT EXISTS idx_players_balance ON players(balance);
            CREATE INDEX IF NOT EXISTS idx_players_level ON players(level);
            CREATE INDEX IF NOT EXISTS idx_pets_player ON pets(player_id);
            CREATE INDEX IF NOT EXISTS idx_seasons_number ON seasons(season_number);
            CREATE INDEX IF NOT EXISTS idx_clan_members_user ON clan_members(user_id);
            CREATE INDEX IF NOT EXISTS idx_clan_members_clan ON clan_members(clan_id);
            CREATE INDEX IF NOT EXISTS idx_duel_challenges_target ON duel_challenges(target_id);
            CREATE INDEX IF NOT EXISTS idx_active_duels_player1 ON active_duels(player1_id, status);
            CREATE INDEX IF NOT EXISTS idx_active_duels_player2 ON active_duels(player2_id, status);
        """)
        
        # Добавляем колонки для старых таблиц
        add_column_if_not_exists(conn, "players", "daily_duels", "INTEGER DEFAULT 0")
        add_column_if_not_exists(conn, "players", "daily_boss_kills", "INTEGER DEFAULT 0")
        add_column_if_not_exists(conn, "players", "daily_coins_earned", "INTEGER DEFAULT 0")
        add_column_if_not_exists(conn, "players", "last_quest_date", "TEXT DEFAULT ''")
        add_column_if_not_exists(conn, "players", "total_duels_won", "INTEGER DEFAULT 0")
        add_column_if_not_exists(conn, "players", "total_boss_kills", "INTEGER DEFAULT 0")
        add_column_if_not_exists(conn, "players", "daily_quest_claimed", "INTEGER DEFAULT 0")
        add_column_if_not_exists(conn, "players", "active_pet_id", "INTEGER")
        add_column_if_not_exists(conn, "players", "season_points", "INTEGER DEFAULT 0")
        add_column_if_not_exists(conn, "players", "title", "TEXT DEFAULT ''")
        add_column_if_not_exists(conn, "players", "current_season", "INTEGER DEFAULT 1")
        add_column_if_not_exists(conn, "players", "last_lottery", "TEXT DEFAULT ''")
        add_column_if_not_exists(conn, "players", "notify_bonus", "INTEGER DEFAULT 1")
        add_column_if_not_exists(conn, "players", "notify_quests", "INTEGER DEFAULT 1")
        add_column_if_not_exists(conn, "players", "notify_boss", "INTEGER DEFAULT 1")
        add_column_if_not_exists(conn, "players", "notify_inactivity", "INTEGER DEFAULT 1")
        add_column_if_not_exists(conn, "players", "last_notify_daily_bonus", "TEXT DEFAULT ''")
        add_column_if_not_exists(conn, "players", "last_notify_quests", "TEXT DEFAULT ''")
        add_column_if_not_exists(conn, "players", "last_notify_boss", "TEXT DEFAULT ''")
        add_column_if_not_exists(conn, "players", "last_notify_inactivity", "TEXT DEFAULT ''")
        
        conn.commit()
    finally:
        conn.close()