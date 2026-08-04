"""
Слой работы с SQLite базой данных.
"""
import os
import sqlite3
import time
import json
from datetime import datetime
from collections import Counter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "game.db")
LEGACY_PLAYERS_FILE = os.path.join(BASE_DIR, "players.json")
LEGACY_DUELS_FILE = os.path.join(BASE_DIR, "duels.json")
LEGACY_BOSS_FILE = os.path.join(BASE_DIR, "boss.json")

# ==================== КОНФИГУРАЦИЯ КВЕСТОВ ====================
DAILY_QUESTS = {
    "duels": {"target": 3, "reward_coins": 100, "reward_exp": 10, "name": "Сыграть 3 дуэли"},
    "boss": {"target": 1, "reward_coins": 150, "reward_exp": 15, "name": "Участвовать в бою с боссом"},
    "coins": {"target": 200, "reward_coins": 50, "reward_exp": 5, "name": "Заработать 200 монет"},
}

ACHIEVEMENTS = {
    "first_blood": {"name": "Первая кровь", "desc": "Выиграть 1 дуэль"},
    "rich": {"name": "Богач", "desc": "Накопить 1000 монет"},
    "boss_slayer": {"name": "Истребитель", "desc": "Убить 3 боссов"},
}


def get_conn():
    conn = sqlite3.connect(DB_FILE, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=10000")
    return conn


def add_column_if_not_exists(conn, table, column, definition):
    try:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
    except sqlite3.OperationalError:
        pass  # Колонка уже существует


def init_db():
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
            CREATE INDEX IF NOT EXISTS idx_inventory_player ON inventory(player_id);
            CREATE INDEX IF NOT EXISTS idx_players_balance ON players(balance);
            CREATE INDEX IF NOT EXISTS idx_players_level ON players(level);
        """)
        
        # Добавляем колонки для квестов, если их нет
        add_column_if_not_exists(conn, "players", "daily_duels", "INTEGER DEFAULT 0")
        add_column_if_not_exists(conn, "players", "daily_boss_kills", "INTEGER DEFAULT 0")
        add_column_if_not_exists(conn, "players", "daily_coins_earned", "INTEGER DEFAULT 0")
        add_column_if_not_exists(conn, "players", "last_quest_date", "TEXT DEFAULT ''")
        add_column_if_not_exists(conn, "players", "total_duels_won", "INTEGER DEFAULT 0")
        add_column_if_not_exists(conn, "players", "total_boss_kills", "INTEGER DEFAULT 0")
        add_column_if_not_exists(conn, "players", "daily_quest_claimed", "INTEGER DEFAULT 0")
        
        conn.commit()
    finally:
        conn.close()


def migrate_from_json():
    if not os.path.exists(LEGACY_PLAYERS_FILE):
        return False
    conn = get_conn()
    try:
        count = conn.execute("SELECT COUNT(*) FROM players").fetchone()[0]
        if count > 0:
            return False
        with open(LEGACY_PLAYERS_FILE, "r", encoding="utf-8") as f:
            old_players = json.load(f)
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
                    (user_id, data.get("name", f"ID{user_id}"), data.get("balance", 100),
                     data.get("level", 1), data.get("exp", 0), data.get("last_work", 0),
                     data.get("last_bonus", ""), data.get("bonus_streak", 0),
                     data.get("last_peer_id"), now, now),
                )
                inventory = data.get("inventory", [])
                counts = Counter(inventory)
                for item_id, qty in counts.items():
                    conn.execute("INSERT OR IGNORE INTO inventory (player_id, item_id, quantity) VALUES (?, ?, ?)", (user_id, item_id, qty))
                equipped = data.get("equipped", {})
                if equipped:
                    conn.execute("INSERT OR IGNORE INTO equipment (player_id, weapon, armor, cosmetic) VALUES (?, ?, ?, ?)",
                                 (user_id, equipped.get("weapon"), equipped.get("armor"), equipped.get("cosmetic")))
                migrated += 1
            except Exception as e:
                print(f"[MIGRATE] Ошибка для игрока {user_id}: {e}")
        conn.commit()
        for path in [LEGACY_PLAYERS_FILE, LEGACY_DUELS_FILE, LEGACY_BOSS_FILE]:
            if os.path.exists(path):
                os.rename(path, path + ".backup")
        return True
    finally:
        conn.close()


# ==================== ИГРОКИ ====================
def get_player(user_id, api_get_name_func):
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM players WHERE user_id = ?", (user_id,)).fetchone()
        if row is None:
            name = api_get_name_func(user_id)
            now = datetime.now().isoformat()
            conn.execute(
                """INSERT INTO players (user_id, name, balance, level, exp, last_work, last_bonus,
                    bonus_streak, last_peer_id, created_at, updated_at)
                   VALUES (?, ?, 100, 1, 0, 0, '', 0, NULL, ?, ?)""", (user_id, name, now, now))
            conn.execute("INSERT OR IGNORE INTO equipment (player_id) VALUES (?)", (user_id,))
            conn.commit()
            row = conn.execute("SELECT * FROM players WHERE user_id = ?", (user_id,)).fetchone()
        return dict(row)
    finally:
        conn.close()


def save_player(player):
    conn = get_conn()
    try:
        player["updated_at"] = datetime.now().isoformat()
        conn.execute(
            """UPDATE players SET name=?, balance=?, level=?, exp=?, last_work=?, last_bonus=?,
               bonus_streak=?, last_peer_id=?, updated_at=?, daily_duels=?, daily_boss_kills=?,
               daily_coins_earned=?, last_quest_date=?, total_duels_won=?, total_boss_kills=?, daily_quest_claimed=?
               WHERE user_id=?""",
            (player["name"], player["balance"], player["level"], player["exp"], player["last_work"],
             player["last_bonus"], player["bonus_streak"], player.get("last_peer_id"), player["updated_at"],
             player.get("daily_duels", 0), player.get("daily_boss_kills", 0), player.get("daily_coins_earned", 0),
             player.get("last_quest_date", ""), player.get("total_duels_won", 0), player.get("total_boss_kills", 0),
             player.get("daily_quest_claimed", 0), player["user_id"]))
        conn.commit()
    finally:
        conn.close()


# ==================== КВЕСТЫ И ДОСТИЖЕНИЯ ====================
def check_and_reset_daily_quests(player):
    today = datetime.now().strftime("%Y-%m-%d")
    if player.get("last_quest_date") != today:
        player["daily_duels"] = 0
        player["daily_boss_kills"] = 0
        player["daily_coins_earned"] = 0
        player["last_quest_date"] = today
        player["daily_quest_claimed"] = 0
        save_player(player)
    return player


def update_daily_progress(user_id, quest_type, amount=1):
    conn = get_conn()
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        if quest_type == "duels":
            conn.execute("UPDATE players SET daily_duels = daily_duels + ? WHERE user_id = ?", (amount, user_id))
        elif quest_type == "boss":
            conn.execute("UPDATE players SET daily_boss_kills = daily_boss_kills + ? WHERE user_id = ?", (amount, user_id))
        elif quest_type == "coins":
            conn.execute("UPDATE players SET daily_coins_earned = daily_coins_earned + ? WHERE user_id = ?", (amount, user_id))
        
        # Сброс флага claim, если день сменился (упрощённо: просто обнуляем claimed при новом дне в get_player, но здесь обновим дату если нужно)
        conn.execute("UPDATE players SET last_quest_date = ?, daily_quest_claimed = 0 WHERE user_id = ? AND last_quest_date != ?", (today, user_id, today))
        conn.commit()
    finally:
        conn.close()


def claim_daily_quests(player):
    if player.get("daily_quest_claimed", 0) == 1:
        return False, "Квесты уже выполнены сегодня!"
    
    today = datetime.now().strftime("%Y-%m-%d")
    if player.get("last_quest_date") != today:
        player = check_and_reset_daily_quests(player)

    total_coins = 0
    total_exp = 0
    completed = []

    for q_type, q_data in DAILY_QUESTS.items():
        current = player.get(f"daily_{q_type}", 0) if q_type != "duels" else player.get("daily_duels", 0)
        # Корректировка ключей: в БД daily_duels, daily_boss_kills, daily_coins_earned
        if q_type == "duels":
            current = player.get("daily_duels", 0)
        elif q_type == "boss":
            current = player.get("daily_boss_kills", 0)
        elif q_type == "coins":
            current = player.get("daily_coins_earned", 0)

        if current >= q_data["target"]:
            total_coins += q_data["reward_coins"]
            total_exp += q_data["reward_exp"]
            completed.append(f"✅ {q_data['name']} (+{q_data['reward_coins']}💰, +{q_data['reward_exp']}⭐)")

    if not completed:
        return False, "Ни один квест ещё не выполнен. Продолжай играть!"

    player["balance"] += total_coins
    player["exp"] += total_exp
    # Простая проверка уровня
    while player["exp"] >= player["level"] * 10:
        player["exp"] -= player["level"] * 10
        player["level"] += 1
    
    player["daily_quest_claimed"] = 1
    save_player(player)
    
    msg = f"🎉 Квесты выполнены!\n\n" + "\n".join(completed)
    msg += f"\n\n💰 Всего: +{total_coins} монет\n⭐ Всего: +{total_exp} опыта"
    return True, msg


def get_daily_quests_status(player):
    today = datetime.now().strftime("%Y-%m-%d")
    if player.get("last_quest_date") != today:
        player = check_and_reset_daily_quests(player)

    lines = ["📜 Ежедневные задания:\n"]
    for q_type, q_data in DAILY_QUESTS.items():
        if q_type == "duels":
            current = player.get("daily_duels", 0)
        elif q_type == "boss":
            current = player.get("daily_boss_kills", 0)
        elif q_type == "coins":
            current = player.get("daily_coins_earned", 0)
        else:
            current = 0
            
        target = q_data["target"]
        status = "✅" if current >= target else "⏳"
        lines.append(f"{status} {q_data['name']} ({current}/{target}) — {q_data['reward_coins']}💰, {q_data['reward_exp']}⭐")
    
    if player.get("daily_quest_claimed", 0) == 1:
        lines.append("\n✅ Награды уже получены сегодня.")
    else:
        lines.append("\n💡 Напиши 'выполнить квесты' чтобы забрать награды за завершённые.")
    
    return "\n".join(lines)


def unlock_achievement(user_id, ach_id, player_name):
    conn = get_conn()
    try:
        # Проверяем, не получено ли уже
        exists = conn.execute("SELECT 1 FROM achievements WHERE user_id = ? AND achievement_id = ?", (user_id, ach_id)).fetchone()
        if exists:
            return None
        
        now = datetime.now().isoformat()
        conn.execute("INSERT INTO achievements (user_id, achievement_id, unlocked_at) VALUES (?, ?, ?)", (user_id, ach_id, now))
        conn.commit()
        return ACHIEVEMENTS.get(ach_id, {}).get("name", ach_id)
    finally:
        conn.close()


def get_achievements_list(user_id):
    conn = get_conn()
    try:
        unlocked = [row["achievement_id"] for row in conn.execute("SELECT achievement_id FROM achievements WHERE user_id = ?", (user_id,)).fetchall()]
        
        lines = ["🏆 Достижения:\n"]
        for ach_id, data in ACHIEVEMENTS.items():
            if ach_id in unlocked:
                lines.append(f"✅ {data['name']}: {data['desc']}")
            else:
                lines.append(f"🔒 {data['name']}: {data['desc']}")
        return "\n".join(lines)
    finally:
        conn.close()


def check_achievements_on_action(user_id, player, action):
    new_achs = []
    if action == "duel_win":
        player["total_duels_won"] = player.get("total_duels_won", 0) + 1
        if player["total_duels_won"] >= 1:
            name = unlock_achievement(user_id, "first_blood", player["name"])
            if name: new_achs.append(name)
    elif action == "rich":
        if player["balance"] >= 1000:
            name = unlock_achievement(user_id, "rich", player["name"])
            if name: new_achs.append(name)
    elif action == "boss_kill":
        player["total_boss_kills"] = player.get("total_boss_kills", 0) + 1
        if player["total_boss_kills"] >= 3:
            name = unlock_achievement(user_id, "boss_slayer", player["name"])
            if name: new_achs.append(name)
    
    if new_achs:
        save_player(player)
    return new_achs


# ==================== ИНВЕНТАРЬ И ЭКИПИРОВКА ====================
def get_inventory(user_id):
    conn = get_conn()
    try:
        rows = conn.execute("SELECT item_id, quantity FROM inventory WHERE player_id = ?", (user_id,)).fetchall()
        return {row["item_id"]: row["quantity"] for row in rows}
    finally:
        conn.close()

def add_to_inventory(user_id, item_id, quantity=1):
    conn = get_conn()
    try:
        conn.execute("""INSERT INTO inventory (player_id, item_id, quantity) VALUES (?, ?, ?)
                        ON CONFLICT(player_id, item_id) DO UPDATE SET quantity = quantity + excluded.quantity""", (user_id, item_id, quantity))
        conn.commit()
    finally:
        conn.close()

def remove_from_inventory(user_id, item_id, quantity=1):
    conn = get_conn()
    try:
        row = conn.execute("SELECT quantity FROM inventory WHERE player_id = ? AND item_id = ?", (user_id, item_id)).fetchone()
        if row is None: return False
        if row["quantity"] <= quantity:
            conn.execute("DELETE FROM inventory WHERE player_id = ? AND item_id = ?", (user_id, item_id))
        else:
            conn.execute("UPDATE inventory SET quantity = quantity - ? WHERE player_id = ? AND item_id = ?", (quantity, user_id, item_id))
        conn.commit()
        return True
    finally:
        conn.close()

def get_equipment(user_id):
    conn = get_conn()
    try:
        row = conn.execute("SELECT weapon, armor, cosmetic FROM equipment WHERE player_id = ?", (user_id,)).fetchone()
        return dict(row) if row else {"weapon": None, "armor": None, "cosmetic": None}
    finally:
        conn.close()

def set_equipment(user_id, slot, item_id):
    conn = get_conn()
    try:
        conn.execute("INSERT OR IGNORE INTO equipment (player_id) VALUES (?)", (user_id,))
        conn.execute(f"UPDATE equipment SET {slot} = ? WHERE player_id = ?", (item_id, user_id))
        conn.commit()
    finally:
        conn.close()


# ==================== ТОП И ДУЭЛИ ====================
def get_top_players(limit=10):
    conn = get_conn()
    try:
        rows = conn.execute("SELECT user_id, name, level, balance, exp FROM players ORDER BY level DESC, balance DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

def get_duel(challenged_id):
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM duels WHERE challenged_id = ?", (challenged_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def save_duel(challenged_id, challenger_id, challenger_peer_id, timestamp):
    conn = get_conn()
    try:
        conn.execute("INSERT OR REPLACE INTO duels (challenged_id, challenger_id, challenger_peer_id, timestamp) VALUES (?, ?, ?, ?)",
                     (challenged_id, challenger_id, challenger_peer_id, timestamp))
        conn.commit()
    finally:
        conn.close()

def delete_duel(challenged_id):
    conn = get_conn()
    try:
        conn.execute("DELETE FROM duels WHERE challenged_id = ?", (challenged_id,))
        conn.commit()
    finally:
        conn.close()


# ==================== БОСС ====================
def get_boss():
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM boss WHERE id = 1").fetchone()
        if row is None: return None
        boss = dict(row)
        boss["participants"] = [dict(r) for r in conn.execute("SELECT * FROM boss_participants WHERE boss_id = 1").fetchall()]
        return boss
    finally:
        conn.close()

def save_boss(boss_data):
    conn = get_conn()
    try:
        conn.execute("""INSERT OR REPLACE INTO boss (id, active, level, name, max_hp, current_hp, attack, defense, start_time)
                        VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?)""",
                     (1 if boss_data.get("active") else 0, boss_data.get("level", 1), boss_data.get("name", ""),
                      boss_data.get("max_hp", 0), boss_data.get("current_hp", 0), boss_data.get("attack", 0),
                      boss_data.get("defense", 0), boss_data.get("start_time")))
        conn.execute("DELETE FROM boss_participants WHERE boss_id = 1")
        participants = boss_data.get("participants", [])
        if isinstance(participants, list):
            for p in participants:
                conn.execute("INSERT INTO boss_participants (boss_id, player_id, name, damage, peer_id) VALUES (1, ?, ?, ?, ?)",
                             (p["player_id"], p["name"], p["damage"], p["peer_id"]))
        elif isinstance(participants, dict):
            for pid_str, pdata in participants.items():
                conn.execute("INSERT INTO boss_participants (boss_id, player_id, name, damage, peer_id) VALUES (1, ?, ?, ?, ?)",
                             (int(pid_str), pdata["name"], pdata["damage"], pdata["peer_id"]))
        conn.commit()
    finally:
        conn.close()

def clear_boss():
    conn = get_conn()
    try:
        conn.execute("DELETE FROM boss WHERE id = 1")
        conn.execute("DELETE FROM boss_participants WHERE boss_id = 1")
        conn.commit()
    finally:
        conn.close()


# Инициализация при импорте
init_db()
migrate_from_json()