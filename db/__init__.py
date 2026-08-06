cd ~/vk-game-bot

# Создай полный db/__init__.py
cat > db/__init__.py << 'ENDOFFILE'
"""
База данных — работа с SQLite.
"""
import sqlite3
from datetime import datetime
from contextlib import contextmanager

DATABASE = "game.db"


@contextmanager
def get_connection():
    """Контекстный менеджер для подключения к БД."""
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
    """Инициализировать базу данных."""
    with get_connection() as conn:
        # Таблица игроков
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
        
        # Таблица предметов
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
        
        # Таблица питомцев
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
        
        # Таблица квестов
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
        
        # Таблица кланов
        conn.execute("""
            CREATE TABLE IF NOT EXISTS clans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                leader_id INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        
        # Таблица участников кланов
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
        
        # ============ ТАБЛИЦЫ PvP ДУЭЛЕЙ ============
        
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
        
        conn.execute("CREATE INDEX IF NOT EXISTS idx_duel_challenges_target ON duel_challenges(target_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_duels_player1 ON duels(player1_id, status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_duels_player2 ON duels(player2_id, status)")


def get_player(user_id, name_fetcher):
    """Получить или создать игрока."""
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
    """Сохранить данные игрока."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE players SET balance = ?, level = ?, season_points = ?, last_work = ?, last_bonus = ? WHERE user_id = ?",
            (player["balance"], player["level"], player["season_points"], 
             player.get("last_work"), player.get("last_bonus"), player["user_id"])
        )


def get_top_players(limit=10):
    """Получить топ игроков по балансу."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM players ORDER BY balance DESC LIMIT ?",
            (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_player_items(user_id):
    """Получить предметы игрока."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM items WHERE user_id = ?",
            (user_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def buy_item(user_id, item_id, quantity=1):
    """Купить предмет."""
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO items (user_id, item_id, quantity) VALUES (?, ?, ?)",
            (user_id, item_id, quantity)
        )


def equip_item(user_id, item_id):
    """Экипировать предмет."""
    with get_connection() as conn:
        conn.execute("UPDATE items SET is_equipped = 0 WHERE user_id = ?", (user_id,))
        conn.execute(
            "UPDATE items SET is_equipped = 1 WHERE user_id = ? AND item_id = ?",
            (user_id, item_id)
        )


def get_player_pets(user_id):
    """Получить питомцев игрока."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM pets WHERE user_id = ?",
            (user_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def buy_pet(user_id, pet_id):
    """Купить питомца."""
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO pets (user_id, pet_id, acquired_at) VALUES (?, ?, ?)",
            (user_id, pet_id, datetime.now().isoformat())
        )


def activate_pet(user_id, pet_id):
    """Активировать питомца."""
    with get_connection() as conn:
        conn.execute("UPDATE pets SET is_active = 0 WHERE user_id = ?", (user_id,))
        conn.execute(
            "UPDATE pets SET is_active = 1 WHERE user_id = ? AND pet_id = ?",
            (user_id, pet_id)
        )


def get_player_quests(user_id):
    """Получить квесты игрока."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM quests WHERE user_id = ?",
            (user_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def complete_quest(user_id, quest_id):
    """Выполнить квест."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE quests SET status = 'completed', completed_at = ? WHERE user_id = ? AND quest_id = ?",
            (datetime.now().isoformat(), user_id, quest_id)
        )


def create_clan(name, leader_id):
    """Создать клан."""
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO clans (name, leader_id, created_at) VALUES (?, ?, ?)",
            (name, leader_id, datetime.now().isoformat())
        )
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def get_clan(user_id):
    """Получить клан игрока."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT c.* FROM clans c JOIN clan_members cm ON c.id = cm.clan_id WHERE cm.user_id = ?",
            (user_id,)
        ).fetchone()
        return dict(row) if row else None


def join_clan(clan_id, user_id):
    """Вступить в клан."""
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO clan_members (clan_id, user_id, joined_at) VALUES (?, ?, ?)",
            (clan_id, user_id, datetime.now().isoformat())
        )


def leave_clan(user_id):
    """Выйти из клана."""
    with get_connection() as conn:
        conn.execute("DELETE FROM clan_members WHERE user_id = ?", (user_id,))


# ============ PvP ДУЭЛИ ============

def create_duel_challenge(challenger_id, target_id):
    """Создать вызов на дуэль."""
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO duel_challenges (challenger_id, target_id, created_at) VALUES (?, ?, ?)",
            (challenger_id, target_id, datetime.now().isoformat())
        )


def get_duel_challenge_for_user(user_id):
    """Получить активный вызов для пользователя."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM duel_challenges WHERE target_id = ? ORDER BY created_at DESC LIMIT 1",
            (user_id,)
        ).fetchone()
        return dict(row) if row else None


def get_duel_challenges_for_user(user_id):
    """Получить все активные вызовы для пользователя."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM duel_challenges WHERE target_id = ? ORDER BY created_at DESC",
            (user_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def clear_duel_challenge(challenge_id):
    """Удалить вызов."""
    with get_connection() as conn:
        conn.execute("DELETE FROM duel_challenges WHERE id = ?", (challenge_id,))


def start_duel(player1_id, player2_id, stake):
    """Начать дуэль."""
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO duels (player1_id, player2_id, stake, status, created_at) VALUES (?, ?, ?, 'active', ?)",
            (player1_id, player2_id, stake, datetime.now().isoformat())
        )


def get_active_duel(user_id):
    """Получить активную дуэль для пользователя."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM duels WHERE (player1_id = ? OR player2_id = ?) AND status = 'active'",
            (user_id, user_id)
        ).fetchone()
        return dict(row) if row else None


def end_duel(duel_id, winner_id):
    """Завершить дуэль."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE duels SET status = 'finished', winner_id = ?, finished_at = ? WHERE id = ?",
            (winner_id, datetime.now().isoformat(), duel_id)
        )


def add_coins_to_player(user_id, amount):
    """Добавить монеты игроку."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE players SET balance = balance + ? WHERE user_id = ?",
            (amount, user_id)
        )
ENDOFFILE

# Создай таблицы
python3 -c "import db; db.init_db(); print('✅ Таблицы созданы!')"

# Проверь что функции есть
python3 -c "import db; print('create_duel_challenge:', hasattr(db, 'create_duel_challenge')); print('start_duel:', hasattr(db, 'start_duel'))"