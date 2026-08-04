"""
Слой работы с SQLite базой данных.
Заменяет JSON-файлы (players.json, duels.json, boss.json).
"""
import os
import sqlite3
import time
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "game.db")
LEGACY_PLAYERS_FILE = os.path.join(BASE_DIR, "players.json")
LEGACY_DUELS_FILE = os.path.join(BASE_DIR, "duels.json")
LEGACY_BOSS_FILE = os.path.join(BASE_DIR, "boss.json")


def get_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Создаёт таблицы если их нет."""
    conn = get_conn()
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

        CREATE INDEX IF NOT EXISTS idx_inventory_player ON inventory(player_id);
        CREATE INDEX IF NOT EXISTS idx_players_balance ON players(balance);
        CREATE INDEX IF NOT EXISTS idx_players_level ON players(level);
    """)
    conn.commit()
    conn.close()


def migrate_from_json():
    """Переносит данные из старых JSON-файлов в БД (одноразово)."""
    if not os.path.exists(LEGACY_PLAYERS_FILE):
        return False

    print(f"[MIGRATE] Найден {LEGACY_PLAYERS_FILE}, начинаем миграцию...")
    conn = get_conn()

    # Проверяем, есть ли уже данные в БД
    count = conn.execute("SELECT COUNT(*) FROM players").fetchone()[0]
    if count > 0:
        print(f"[MIGRATE] В БД уже есть {count} игроков, миграция пропущена.")
        conn.close()
        return False

    try:
        with open(LEGACY_PLAYERS_FILE, "r", encoding="utf-8") as f:
            old_players = json.load(f)
    except Exception as e:
        print(f"[MIGRATE] Ошибка чтения JSON: {e}")
        conn.close()
        return False

    now = datetime.now().isoformat()
    migrated = 0

    for user_id_str, data in old_players.items():
        try:
            user_id = int(user_id_str)
            conn.execute(
                """INSERT OR IGNORE INTO players
                   (user_id, name, balance, level, exp, last_work, last_bonus,
                    bonus_streak, last_peer_id, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    user_id,
                    data.get("name", f"ID{user_id}"),
                    data.get("balance", 100),
                    data.get("level", 1),
                    data.get("exp", 0),
                    data.get("last_work", 0),
                    data.get("last_bonus", ""),
                    data.get("bonus_streak", 0),
                    data.get("last_peer_id"),
                    now,
                    now,
                ),
            )

            # Инвентарь
            inventory = data.get("inventory", [])
            from collections import Counter
            counts = Counter(inventory)
            for item_id, qty in counts.items():
                conn.execute(
                    """INSERT OR IGNORE INTO inventory (player_id, item_id, quantity)
                       VALUES (?, ?, ?)""",
                    (user_id, item_id, qty),
                )

            # Экипировка
            equipped = data.get("equipped", {})
            if equipped:
                conn.execute(
                    """INSERT OR IGNORE INTO equipment (player_id, weapon, armor, cosmetic)
                       VALUES (?, ?, ?, ?)""",
                    (
                        user_id,
                        equipped.get("weapon"),
                        equipped.get("armor"),
                        equipped.get("cosmetic"),
                    ),
                )

            migrated += 1
        except Exception as e:
            print(f"[MIGRATE] Ошибка для игрока {user_id}: {e}")

    # Миграция дуэлей
    if os.path.exists(LEGACY_DUELS_FILE):
        try:
            with open(LEGACY_DUELS_FILE, "r", encoding="utf-8") as f:
                old_duels = json.load(f)
            for challenged_str, data in old_duels.items():
                conn.execute(
                    """INSERT OR IGNORE INTO duels
                       (challenged_id, challenger_id, challenger_peer_id, timestamp)
                       VALUES (?, ?, ?, ?)""",
                    (
                        int(challenged_str),
                        data["challenger_id"],
                        data["challenger_peer_id"],
                        data["timestamp"],
                    ),
                )
        except Exception as e:
            print(f"[MIGRATE] Ошибка миграции дуэлей: {e}")

    # Миграция босса
    if os.path.exists(LEGACY_BOSS_FILE):
        try:
            with open(LEGACY_BOSS_FILE, "r", encoding="utf-8") as f:
                old_boss = json.load(f)
            if old_boss and old_boss.get("active"):
                conn.execute(
                    """INSERT OR REPLACE INTO boss
                       (id, active, level, name, max_hp, current_hp, attack, defense, start_time)
                       VALUES (1, 1, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        old_boss.get("level", 1),
                        old_boss.get("name", ""),
                        old_boss.get("max_hp", 0),
                        old_boss.get("current_hp", 0),
                        old_boss.get("attack", 0),
                        old_boss.get("defense", 0),
                        old_boss.get("start_time"),
                    ),
                )
                for pid_str, pdata in old_boss.get("participants", {}).items():
                    conn.execute(
                        """INSERT OR IGNORE INTO boss_participants
                           (boss_id, player_id, name, damage, peer_id)
                           VALUES (1, ?, ?, ?, ?)""",
                        (int(pid_str), pdata["name"], pdata["damage"], pdata["peer_id"]),
                    )
        except Exception as e:
            print(f"[MIGRATE] Ошибка миграции босса: {e}")

    conn.commit()
    conn.close()
    print(f"[MIGRATE] Мигрировано игроков: {migrated}")

    # Переименовываем старые файлы (чтобы не мигрировать повторно)
    for path in [LEGACY_PLAYERS_FILE, LEGACY_DUELS_FILE, LEGACY_BOSS_FILE]:
        if os.path.exists(path):
            backup = path + ".backup"
            os.rename(path, backup)
            print(f"[MIGRATE] {path} -> {backup}")

    return True


# ==================== ИГРОКИ ====================
def get_player(user_id, api_get_name_func):
    conn = get_conn()
    row = conn.execute("SELECT * FROM players WHERE user_id = ?", (user_id,)).fetchone()
    if row is None:
        name = api_get_name_func(user_id)
        now = datetime.now().isoformat()
        conn.execute(
            """INSERT INTO players
               (user_id, name, balance, level, exp, last_work, last_bonus,
                bonus_streak, last_peer_id, created_at, updated_at)
               VALUES (?, ?, 100, 1, 0, 0, '', 0, NULL, ?, ?)""",
            (user_id, name, now, now),
        )
        conn.execute(
            "INSERT OR IGNORE INTO equipment (player_id) VALUES (?)", (user_id,)
        )
        conn.commit()
        row = conn.execute("SELECT * FROM players WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row)


def save_player(player):
    conn = get_conn()
    player["updated_at"] = datetime.now().isoformat()
    conn.execute(
        """UPDATE players SET
           name=?, balance=?, level=?, exp=?, last_work=?, last_bonus=?,
           bonus_streak=?, last_peer_id=?, updated_at=?
           WHERE user_id=?""",
        (
            player["name"],
            player["balance"],
            player["level"],
            player["exp"],
            player["last_work"],
            player["last_bonus"],
            player["bonus_streak"],
            player.get("last_peer_id"),
            player["updated_at"],
            player["user_id"],
        ),
    )
    conn.commit()
    conn.close()


def get_inventory(user_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT item_id, quantity FROM inventory WHERE player_id = ?", (user_id,)
    ).fetchall()
    conn.close()
    return {row["item_id"]: row["quantity"] for row in rows}


def add_to_inventory(user_id, item_id, quantity=1):
    conn = get_conn()
    conn.execute(
        """INSERT INTO inventory (player_id, item_id, quantity)
           VALUES (?, ?, ?)
           ON CONFLICT(player_id, item_id) DO UPDATE SET
           quantity = quantity + excluded.quantity""",
        (user_id, item_id, quantity),
    )
    conn.commit()
    conn.close()


def remove_from_inventory(user_id, item_id, quantity=1):
    conn = get_conn()
    row = conn.execute(
        "SELECT quantity FROM inventory WHERE player_id = ? AND item_id = ?",
        (user_id, item_id),
    ).fetchone()
    if row is None:
        conn.close()
        return False
    if row["quantity"] <= quantity:
        conn.execute(
            "DELETE FROM inventory WHERE player_id = ? AND item_id = ?",
            (user_id, item_id),
        )
    else:
        conn.execute(
            """UPDATE inventory SET quantity = quantity - ?
               WHERE player_id = ? AND item_id = ?""",
            (quantity, user_id, item_id),
        )
    conn.commit()
    conn.close()
    return True


def get_equipment(user_id):
    conn = get_conn()
    row = conn.execute(
        "SELECT weapon, armor, cosmetic FROM equipment WHERE player_id = ?", (user_id,)
    ).fetchone()
    conn.close()
    if row is None:
        return {"weapon": None, "armor": None, "cosmetic": None}
    return dict(row)


def set_equipment(user_id, slot, item_id):
    conn = get_conn()
    conn.execute(
        "INSERT OR IGNORE INTO equipment (player_id) VALUES (?)", (user_id,)
    )
    conn.execute(
        f"UPDATE equipment SET {slot} = ? WHERE player_id = ?",
        (item_id, user_id),
    )
    conn.commit()
    conn.close()


# ==================== ТОП ====================
def get_top_players(limit=10):
    conn = get_conn()
    rows = conn.execute(
        """SELECT user_id, name, level, balance, exp
           FROM players ORDER BY level DESC, balance DESC LIMIT ?""",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ==================== ДУЭЛИ ====================
def get_duel(challenged_id):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM duels WHERE challenged_id = ?", (challenged_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def save_duel(challenged_id, challenger_id, challenger_peer_id, timestamp):
    conn = get_conn()
    conn.execute(
        """INSERT OR REPLACE INTO duels
           (challenged_id, challenger_id, challenger_peer_id, timestamp)
           VALUES (?, ?, ?, ?)""",
        (challenged_id, challenger_id, challenger_peer_id, timestamp),
    )
    conn.commit()
    conn.close()


def delete_duel(challenged_id):
    conn = get_conn()
    conn.execute("DELETE FROM duels WHERE challenged_id = ?", (challenged_id,))
    conn.commit()
    conn.close()


# ==================== БОСС ====================
def get_boss():
    conn = get_conn()
    row = conn.execute("SELECT * FROM boss WHERE id = 1").fetchone()
    if row is None:
        conn.close()
        return None
    boss = dict(row)
    boss["participants"] = [
        dict(r)
        for r in conn.execute(
            "SELECT * FROM boss_participants WHERE boss_id = 1"
        ).fetchall()
    ]
    conn.close()
    return boss


def save_boss(boss_data):
    conn = get_conn()
    conn.execute(
        """INSERT OR REPLACE INTO boss
           (id, active, level, name, max_hp, current_hp, attack, defense, start_time)
           VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            1 if boss_data.get("active") else 0,
            boss_data.get("level", 1),
            boss_data.get("name", ""),
            boss_data.get("max_hp", 0),
            boss_data.get("current_hp", 0),
            boss_data.get("attack", 0),
            boss_data.get("defense", 0),
            boss_data.get("start_time"),
        ),
    )

    # Обновляем участников
    conn.execute("DELETE FROM boss_participants WHERE boss_id = 1")
    for pid_str, pdata in boss_data.get("participants", {}).items():
        conn.execute(
            """INSERT INTO boss_participants
               (boss_id, player_id, name, damage, peer_id)
               VALUES (1, ?, ?, ?, ?)""",
            (int(pid_str), pdata["name"], pdata["damage"], pdata["peer_id"]),
        )

    conn.commit()
    conn.close()


def clear_boss():
    conn = get_conn()
    conn.execute("DELETE FROM boss WHERE id = 1")
    conn.execute("DELETE FROM boss_participants WHERE boss_id = 1")
    conn.commit()
    conn.close()


# Инициализация при импорте
init_db()
migrate_from_json()