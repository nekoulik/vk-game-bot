"""Функции для работы с боссом."""
from db.base import get_conn


def get_boss():
    """Получить текущего босса."""
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM boss WHERE id = 1").fetchone()
        if row is None:
            return None
        boss = dict(row)
        boss["participants"] = [dict(r) for r in conn.execute("SELECT * FROM boss_participants WHERE boss_id = 1").fetchall()]
        return boss
    finally:
        conn.close()


def save_boss(boss_data):
    """Сохранить данные босса."""
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
        conn.commit()
    finally:
        conn.close()


def clear_boss():
    """Удалить текущего босса."""
    conn = get_conn()
    try:
        conn.execute("DELETE FROM boss WHERE id = 1")
        conn.execute("DELETE FROM boss_participants WHERE boss_id = 1")
        conn.commit()
    finally:
        conn.close()