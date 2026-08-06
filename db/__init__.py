"""
База данных — работа с SQLite.
"""
import sqlite3
from datetime import datetime
from contextlib import contextmanager

DATABASE = "game.db"


@contextmanager
def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS players (
                user_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                balance INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                season_points INTEGER DEFAULT 0,
                last_work TEXT,
                last_bonus TEXT,
                created_at TEXT NOT NULL
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                item_id INTEGER NOT NULL,
                quantity INTEGER DEFAULT 1,
                is_equipped INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES players(user_id)
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                pet_id INTEGER NOT NULL,
                is_active INTEGER DEFAULT 0,
                acquired_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES players(user_id)
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS quests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                quest_id INTEGER NOT NULL,
                status TEXT DEFAULT 'active',
                progress INTEGER DEFAULT 0,
                completed_at TEXT,
                FOREIGN KEY (user_id) REFERENCES players(user_id)
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS clans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                leader_id INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS clan_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                clan_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                role TEXT DEFAULT 'member',
                joined_at TEXT NOT NULL,
                FOREIGN KEY (clan_id) REFERENCES clans(id),
                FOREIGN KEY (user_id) REFERENCES players(user_id)
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS duel_challenges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                challenger_id INTEGER NOT NULL,
                target_id INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS duels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player1_id INTEGER NOT NULL,
                player2_id INTEGER NOT NULL,
                stake INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                winner_id INTEGER,
                created_at TEXT NOT NULL,
                finished_at TEXT
            )
        """)
        
        # Таблица босса
        conn.execute("""
            CREATE TABLE IF NOT EXISTS boss (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                hp INTEGER DEFAULT 1000,
                max_hp INTEGER DEFAULT 1000,
                status TEXT DEFAULT 'waiting',
                started_at TEXT,
                finished_at TEXT,
                winner_id INTEGER
            )
        """)
        
        # Участники боя с боссом
        conn.execute("""
            CREATE TABLE IF NOT EXISTS boss_participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                boss_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                damage INTEGER DEFAULT 0,
                FOREIGN KEY (boss_id) REFERENCES boss(id),
                FOREIGN KEY (user_id) REFERENCES players(user_id)
            )
        """)
        
        # Достижения
        conn.execute("""
            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                achievement_id INTEGER NOT NULL,
                unlocked_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES players(user_id)
            )
        """)
        
        # Сезоны
        conn.execute("""
            CREATE TABLE IF NOT EXISTS seasons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                number INTEGER NOT NULL UNIQUE,
                started_at TEXT NOT NULL,
                ended_at TEXT,
                winner_id INTEGER
            )
        """)
        
        # Инвентарь
        conn.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                item_id INTEGER NOT NULL,
                quantity INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES players(user_id)
            )
        """)
        
        # Экипировка
        conn.execute("""
            CREATE TABLE IF NOT EXISTS equipment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                item_id INTEGER NOT NULL,
                slot TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES players(user_id)
            )
        """)
        
        # Кланы-войны
        conn.execute("""
            CREATE TABLE IF NOT EXISTS clan_wars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                clan1_id INTEGER NOT NULL,
                clan2_id INTEGER NOT NULL,
                status TEXT DEFAULT 'active',
                started_at TEXT NOT NULL,
                FOREIGN KEY (clan1_id) REFERENCES clans(id),
                FOREIGN KEY (clan2_id) REFERENCES clans(id)
            )
        """)
        
        conn.execute("CREATE INDEX IF NOT EXISTS idx_duel_challenges_target ON duel_challenges(target_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_duels_player1 ON duels(player1_id, status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_boss_participants_boss ON boss_participants(boss_id)")
        
        # Инициализируем босса если нет
        conn.execute("INSERT OR IGNORE INTO boss (id, hp, max_hp, status) VALUES (1, 1000, 1000, 'waiting')")


# ============ ИГРОКИ ============

def get_player(user_id, name_fetcher):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM players WHERE user_id = ?", (user_id,)).fetchone()
        if not row:
            name = name_fetcher(user_id)
            conn.execute(
                "INSERT INTO players (user_id, name, created_at) VALUES (?, ?, ?)",
                (user_id, name, datetime.now().isoformat())
            )
            row = conn.execute("SELECT * FROM players WHERE user_id = ?", (user_id,)).fetchone()
        return dict(row)


def save_player(player):
    with get_connection() as conn:
        conn.execute(
            "UPDATE players SET balance = ?, level = ?, season_points = ?, last_work = ?, last_bonus = ? WHERE user_id = ?",
            (player["balance"], player["level"], player["season_points"], 
             player.get("last_work"), player.get("last_bonus"), player["user_id"])
        )


def get_top_players(limit=10):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM players ORDER BY balance DESC LIMIT ?",
            (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_all_players():
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM players").fetchall()
        return [dict(r) for r in rows]


# ============ ПРЕДМЕТЫ ============

def get_player_items(user_id):
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM items WHERE user_id = ?", (user_id,)).fetchall()
        return [dict(r) for r in rows]


def buy_item(user_id, item_id, quantity=1):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO items (user_id, item_id, quantity) VALUES (?, ?, ?)",
            (user_id, item_id, quantity)
        )


def equip_item(user_id, item_id):
    with get_connection() as conn:
        conn.execute("UPDATE items SET is_equipped = 0 WHERE user_id = ?", (user_id,))
        conn.execute(
            "UPDATE items SET is_equipped = 1 WHERE user_id = ? AND item_id = ?",
            (user_id, item_id)
        )


# ============ ПИТОМЦЫ ============

def get_player_pets(user_id):
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM pets WHERE user_id = ?", (user_id,)).fetchall()
        return [dict(r) for r in rows]


def buy_pet(user_id, pet_id):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO pets (user_id, pet_id, acquired_at) VALUES (?, ?, ?)",
            (user_id, pet_id, datetime.now().isoformat())
        )


def activate_pet(user_id, pet_id):
    with get_connection() as conn:
        conn.execute("UPDATE pets SET is_active = 0 WHERE user_id = ?", (user_id,))
        conn.execute(
            "UPDATE pets SET is_active = 1 WHERE user_id = ? AND pet_id = ?",
            (user_id, pet_id)
        )


# ============ КВЕСТЫ ============

def get_player_quests(user_id):
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM quests WHERE user_id = ?", (user_id,)).fetchall()
        return [dict(r) for r in rows]


def complete_quest(user_id, quest_id):
    with get_connection() as conn:
        conn.execute(
            "UPDATE quests SET status = 'completed', completed_at = ? WHERE user_id = ? AND quest_id = ?",
            (datetime.now().isoformat(), user_id, quest_id)
        )


# ============ КЛАНЫ ============

def create_clan(name, leader_id):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO clans (name, leader_id, created_at) VALUES (?, ?, ?)",
            (name, leader_id, datetime.now().isoformat())
        )
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def get_clan(user_id):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT c.* FROM clans c JOIN clan_members cm ON c.id = cm.clan_id WHERE cm.user_id = ?",
            (user_id,)
        ).fetchone()
        return dict(row) if row else None


def get_all_clans():
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM clans").fetchall()
        return [dict(r) for r in rows]


def join_clan(clan_id, user_id):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO clan_members (clan_id, user_id, joined_at) VALUES (?, ?, ?)",
            (clan_id, user_id, datetime.now().isoformat())
        )


def leave_clan(user_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM clan_members WHERE user_id = ?", (user_id,))


def get_clan_members(clan_id):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT cm.*, p.name FROM clan_members cm JOIN players p ON cm.user_id = p.user_id WHERE cm.clan_id = ?",
            (clan_id,)
        ).fetchall()
        return [dict(r) for r in rows]


# ============ PvP ДУЭЛИ ============

def create_duel_challenge(challenger_id, target_id):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO duel_challenges (challenger_id, target_id, created_at) VALUES (?, ?, ?)",
            (challenger_id, target_id, datetime.now().isoformat())
        )


def get_duel_challenge_for_user(user_id):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM duel_challenges WHERE target_id = ? ORDER BY created_at DESC LIMIT 1",
            (user_id,)
        ).fetchone()
        return dict(row) if row else None


def get_duel_challenges_for_user(user_id):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM duel_challenges WHERE target_id = ? ORDER BY created_at DESC",
            (user_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def clear_duel_challenge(challenge_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM duel_challenges WHERE id = ?", (challenge_id,))


def start_duel(player1_id, player2_id, stake):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO duels (player1_id, player2_id, stake, status, created_at) VALUES (?, ?, ?, 'active', ?)",
            (player1_id, player2_id, stake, datetime.now().isoformat())
        )


def get_active_duel(user_id):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM duels WHERE (player1_id = ? OR player2_id = ?) AND status = 'active'",
            (user_id, user_id)
        ).fetchone()
        return dict(row) if row else None


def end_duel(duel_id, winner_id):
    with get_connection() as conn:
        conn.execute(
            "UPDATE duels SET status = 'finished', winner_id = ?, finished_at = ? WHERE id = ?",
            (winner_id, datetime.now().isoformat(), duel_id)
        )


def add_coins_to_player(user_id, amount):
    with get_connection() as conn:
        conn.execute(
            "UPDATE players SET balance = balance + ? WHERE user_id = ?",
            (amount, user_id)
        )


# ============ БОСС ============

def get_boss():
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM boss WHERE id = 1").fetchone()
        return dict(row) if row else None


def start_boss():
    with get_connection() as conn:
        conn.execute(
            "UPDATE boss SET hp = max_hp, status = 'active', started_at = ?, winner_id = NULL, finished_at = NULL WHERE id = 1",
            (datetime.now().isoformat(),)
        )


def attack_boss(user_id, damage):
    with get_connection() as conn:
        conn.execute(
            "UPDATE boss SET hp = hp - ? WHERE id = 1 AND status = 'active'",
            (damage,)
        )
        boss = conn.execute("SELECT hp FROM boss WHERE id = 1").fetchone()
        
        # Записываем урон участника
        conn.execute(
            "INSERT INTO boss_participants (boss_id, user_id, damage) VALUES (1, ?, ?)",
            (user_id, damage)
        )
        
        # Если босс умер
        if boss and boss["hp"] <= 0:
            conn.execute(
                "UPDATE boss SET status = 'dead', finished_at = ?, winner_id = ? WHERE id = 1",
                (datetime.now().isoformat(), user_id)
            )
            return True
        return False


def get_boss_participants():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT bp.*, p.name FROM boss_participants bp JOIN players p ON bp.user_id = p.user_id WHERE bp.boss_id = 1 ORDER BY bp.damage DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def reset_boss():
    with get_connection() as conn:
        conn.execute("DELETE FROM boss_participants WHERE boss_id = 1")
        conn.execute(
            "UPDATE boss SET hp = max_hp, status = 'waiting', started_at = NULL, finished_at = NULL, winner_id = NULL WHERE id = 1"
        )


# ============ ДОСТИЖЕНИЯ ============

def get_player_achievements(user_id):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM achievements WHERE user_id = ?",
            (user_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def unlock_achievement(user_id, achievement_id):
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT id FROM achievements WHERE user_id = ? AND achievement_id = ?",
            (user_id, achievement_id)
        ).fetchone()
        if not existing:
            conn.execute(
                "INSERT INTO achievements (user_id, achievement_id, unlocked_at) VALUES (?, ?, ?)",
                (user_id, achievement_id, datetime.now().isoformat())
            )


# ============ СЕЗОНЫ ============

def get_current_season():
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM seasons WHERE ended_at IS NULL ORDER BY number DESC LIMIT 1"
        ).fetchone()
        return dict(row) if row else None


def get_seasons_history():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM seasons ORDER BY number DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def start_season(number):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO seasons (number, started_at) VALUES (?, ?)",
            (number, datetime.now().isoformat())
        )


def end_season(season_id, winner_id):
    with get_connection() as conn:
        conn.execute(
            "UPDATE seasons SET ended_at = ?, winner_id = ? WHERE id = ?",
            (datetime.now().isoformat(), winner_id, season_id)
        )


def reset_season():
    with get_connection() as conn:
        conn.execute("UPDATE players SET season_points = 0")