"""Функции для работы с игроками."""
import os
import json
from datetime import datetime
from collections import Counter
from db.base import get_conn, BASE_DIR

LEGACY_PLAYERS_FILE = os.path.join(BASE_DIR, "players.json")
LEGACY_DUELS_FILE = os.path.join(BASE_DIR, "duels.json")
LEGACY_BOSS_FILE = os.path.join(BASE_DIR, "boss.json")


def migrate_from_json():
    """Миграция со старых JSON файлов."""
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


def get_player(user_id, api_get_name_func):
    """Получить игрока по ID."""
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
    """Сохранить игрока."""
    conn = get_conn()
    try:
        player["updated_at"] = datetime.now().isoformat()
        conn.execute(
            """UPDATE players SET name=?, balance=?, level=?, exp=?, last_work=?, last_bonus=?,
               bonus_streak=?, last_peer_id=?, updated_at=?, daily_duels=?, daily_boss_kills=?,
               daily_coins_earned=?, last_quest_date=?, total_duels_won=?, total_boss_kills=?, 
               daily_quest_claimed=?, season_points=?, title=?, current_season=?, last_lottery=?,
               mute_until=?, last_activity=?
               WHERE user_id=?""",
            (player["name"], player["balance"], player["level"], player["exp"], player["last_work"],
             player["last_bonus"], player["bonus_streak"], player.get("last_peer_id"), player["updated_at"],
             player.get("daily_duels", 0), player.get("daily_boss_kills", 0), player.get("daily_coins_earned", 0),
             player.get("last_quest_date", ""), player.get("total_duels_won", 0), player.get("total_boss_kills", 0),
             player.get("daily_quest_claimed", 0), player.get("season_points", 0), player.get("title", ""),
             player.get("current_season", 1), player.get("last_lottery", ""),
             int(player.get("mute_until", 0)),
             player.get("last_activity", ""),
             player["user_id"]))
        conn.commit()
    finally:
        conn.close()


def check_and_reset_daily_quests(player):
    """Проверить и сбросить ежедневные квесты."""
    today = datetime.now().strftime("%Y-%m-%d")
    if player.get("last_quest_date") != today:
        player["daily_duels"] = 0
        player["daily_boss_kills"] = 0
        player["daily_coins_earned"] = 0
        player["last_quest_date"] = today
        player["daily_quest_claimed"] = 0
        save_player(player)
    return player


def get_all_players():
    """Получить всех игроков."""
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT user_id, name, balance, level, exp, season_points, title, last_bonus, bonus_streak, mute_until "
            "FROM players ORDER BY level DESC, balance DESC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def add_coins_to_player(user_id, amount):
    """Выдать монеты игроку."""
    conn = get_conn()
    try:
        conn.execute(
            "UPDATE players SET balance = balance + ? WHERE user_id = ?",
            (amount, user_id)
        )
        conn.commit()
        return conn.total_changes > 0
    finally:
        conn.close()


def ban_player(user_id):
    """Забанить игрока."""
    conn = get_conn()
    try:
        conn.execute(
            "UPDATE players SET balance = -1, mute_until = 0 WHERE user_id = ?",
            (user_id,)
        )
        conn.commit()
        return conn.total_changes > 0
    finally:
        conn.close()


def unban_player(user_id):
    """Разбанить игрока."""
    conn = get_conn()
    try:
        conn.execute(
            "UPDATE players SET balance = 100, mute_until = 0 WHERE user_id = ? AND balance = -1",
            (user_id,)
        )
        conn.commit()
        return conn.total_changes > 0
    finally:
        conn.close()


def is_player_banned(user_id):
    """Проверить, забанен ли игрок."""
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT balance FROM players WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        return row and row["balance"] == -1
    finally:
        conn.close()


def get_stats():
    """Получить общую статистику."""
    conn = get_conn()
    try:
        total_players = conn.execute("SELECT COUNT(*) FROM players").fetchone()[0]
        total_coins = conn.execute("SELECT SUM(balance) FROM players WHERE balance > 0").fetchone()[0] or 0
        avg_level = conn.execute("SELECT AVG(level) FROM players").fetchone()[0] or 0
        total_duels = conn.execute("SELECT SUM(total_duels_won) FROM players").fetchone()[0] or 0
        total_boss_kills = conn.execute("SELECT SUM(total_boss_kills) FROM players").fetchone()[0] or 0
        
        return {
            "total_players": total_players,
            "total_coins": total_coins,
            "avg_level": round(avg_level, 2),
            "total_duels": total_duels,
            "total_boss_kills": total_boss_kills,
        }
    finally:
        conn.close()


def get_top_players(limit=10):
    """Получить топ игроков."""
    conn = get_conn()
    try:
        rows = conn.execute("SELECT user_id, name, level, balance, exp FROM players ORDER BY level DESC, balance DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def update_daily_progress(user_id, quest_type, amount=1):
    """Обновить прогресс ежедневных квестов."""
    conn = get_conn()
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        if quest_type == "duels":
            conn.execute("UPDATE players SET daily_duels = daily_duels + ? WHERE user_id = ?", (amount, user_id))
        elif quest_type == "boss":
            conn.execute("UPDATE players SET daily_boss_kills = daily_boss_kills + ? WHERE user_id = ?", (amount, user_id))
        elif quest_type == "coins":
            conn.execute("UPDATE players SET daily_coins_earned = daily_coins_earned + ? WHERE user_id = ?", (amount, user_id))
        conn.execute("UPDATE players SET last_quest_date = ?, daily_quest_claimed = 0 WHERE user_id = ? AND last_quest_date != ?", (today, user_id, today))
        conn.commit()
    finally:
        conn.close()


def get_all_peer_ids():
    """Получить все peer_id игроков."""
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT user_id, last_peer_id FROM players WHERE last_peer_id IS NOT NULL"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()