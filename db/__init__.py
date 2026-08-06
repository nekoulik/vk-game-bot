<<<<<<< HEAD
"""
Пакет db — слой работы с базой данных.
Все функции импортируются из подмодулей для удобства.
=======
cd ~/vk-game-bot

# Удали старый файл
rm -f db/__init__.py

# Создай файл через Python (надёжно!)
python3 << 'PYEOF'
content = '''"""
База данных — работа с SQLite.
>>>>>>> 0726ca62eb2eff084ccfa6e61739e2a916370bc0
"""

# Базовые функции
from db.base import get_conn, add_column_if_not_exists, init_db

# Игроки
from db.players import (
    migrate_from_json,
    get_player,
    save_player,
    check_and_reset_daily_quests,
    get_all_players,
    add_coins_to_player,
    ban_player,
    unban_player,
    is_player_banned,
    get_stats,
    get_top_players,
    update_daily_progress,
    get_all_peer_ids,
)

# Предметы и инвентарь
from db.items import (
    get_inventory,
    add_to_inventory,
    remove_from_inventory,
    get_equipment,
    set_equipment,
)

# Питомцы
from db.pets import (
    get_player_pets,
    buy_pet,
    activate_pet,
    get_active_pet,
    get_pet_bonus,
)

# Босс
from db.boss import (
    get_boss,
    save_boss,
    clear_boss,
)

# Дуэли
from db.duels import (
    get_duel,
    save_duel,
    delete_duel,
    create_duel_challenge,
    get_duel_challenge_for_user,
    get_duel_challenges_for_user,
    clear_duel_challenge,
    start_duel,
    get_active_duel,
    end_duel,
)

# Квесты и достижения
from db.quests import (
    claim_daily_quests,
    get_daily_quests_status,
    unlock_achievement,
    get_achievements_list,
    check_achievements_on_action,
)

# Сезоны
from db.seasons import (
    get_current_season,
    get_current_season_number,
    check_and_reset_season,
    add_season_points,
    get_season_leaderboard,
    get_season_history,
    force_reset_season,
)

# Кланы
from db.clans import (
    create_clan,
    get_clan,
    get_clan_by_id,
    get_clan_members,
    invite_to_clan,
    leave_clan,
    kick_from_clan,
    disband_clan,
    get_all_clans,
    add_clan_exp,
    get_clan_bonus,
    start_clan_war,
    end_clan_war,
)

# Уведомления
from db.notifications import (
    NOTIFICATION_TYPES,
    get_notification_settings,
    set_notification_setting,
    get_last_notification_time,
    update_last_notification,
    should_notify,
    get_inactive_players,
)


<<<<<<< HEAD
# Автоматическая инициализация при импорте
init_db()
migrate_from_json()
=======
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
        
        conn.execute("CREATE INDEX IF NOT EXISTS idx_duel_challenges_target ON duel_challenges(target_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_duels_player1 ON duels(player1_id, status)")


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


def join_clan(clan_id, user_id):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO clan_members (clan_id, user_id, joined_at) VALUES (?, ?, ?)",
            (clan_id, user_id, datetime.now().isoformat())
        )


def leave_clan(user_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM clan_members WHERE user_id = ?", (user_id,))


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
'''

with open('db/__init__.py', 'w') as f:
    f.write(content)
print("✅ Файл db/__init__.py создан через Python!")
PYEOF

# Проверь что файл правильный
head -3 db/__init__.py

# Создай БД
python3 -c "import db; db.init_db(); print('✅ БД создана')"

# Проверь функции
python3 -c "import db; print('create_duel_challenge:', hasattr(db, 'create_duel_challenge'))"

# Запусти бота
pkill -f main.py
python3 main.py > bot.log 2>&1 &

sleep 2
tail -20 bot.log
>>>>>>> 0726ca62eb2eff084ccfa6e61739e2a916370bc0
