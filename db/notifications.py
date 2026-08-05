"""Функции для работы с уведомлениями."""
from datetime import datetime, timedelta
from db.base import get_conn

NOTIFICATION_TYPES = {
    "daily_bonus": "Ежедневный бонус",
    "quests": "Невыполненные квесты",
    "boss": "Появление босса",
    "inactivity": "Напоминание о неактивности",
}


def get_notification_settings(user_id):
    """Получить настройки уведомлений игрока."""
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT notify_bonus, notify_quests, notify_boss, notify_inactivity "
            "FROM players WHERE user_id = ?", (user_id,)
        ).fetchone()
        if row:
            return {
                "daily_bonus": bool(row["notify_bonus"]),
                "quests": bool(row["notify_quests"]),
                "boss": bool(row["notify_boss"]),
                "inactivity": bool(row["notify_inactivity"]),
            }
        return None
    finally:
        conn.close()


def set_notification_setting(user_id, notification_type, enabled):
    """Включить/выключить уведомление."""
    conn = get_conn()
    try:
        col_map = {
            "daily_bonus": "notify_bonus",
            "quests": "notify_quests",
            "boss": "notify_boss",
            "inactivity": "notify_inactivity",
        }
        col_name = col_map.get(notification_type)
        if col_name:
            conn.execute(
                f"UPDATE players SET {col_name} = ? WHERE user_id = ?",
                (1 if enabled else 0, user_id)
            )
            conn.commit()
    finally:
        conn.close()


def get_last_notification_time(user_id, notification_type):
    """Получить время последнего уведомления."""
    conn = get_conn()
    try:
        col_map = {
            "daily_bonus": "last_notify_daily_bonus",
            "quests": "last_notify_quests",
            "boss": "last_notify_boss",
            "inactivity": "last_notify_inactivity",
        }
        col_name = col_map.get(notification_type)
        if col_name:
            row = conn.execute(
                f"SELECT {col_name} FROM players WHERE user_id = ?",
                (user_id,)
            ).fetchone()
            if row:
                return row[col_name]
        return None
    finally:
        conn.close()


def update_last_notification(user_id, notification_type):
    """Обновить время последнего уведомления."""
    conn = get_conn()
    try:
        now = datetime.now().isoformat()
        col_map = {
            "daily_bonus": "last_notify_daily_bonus",
            "quests": "last_notify_quests",
            "boss": "last_notify_boss",
            "inactivity": "last_notify_inactivity",
        }
        col_name = col_map.get(notification_type)
        if col_name:
            conn.execute(
                f"UPDATE players SET {col_name} = ? WHERE user_id = ?",
                (now, user_id)
            )
            conn.commit()
    finally:
        conn.close()


def should_notify(user_id, notification_type, cooldown_hours=24):
    """Проверить, можно ли отправить уведомление (прошла ли кулдаун)."""
    settings = get_notification_settings(user_id)
    if not settings or not settings.get(notification_type, False):
        return False
    
    last_time = get_last_notification_time(user_id, notification_type)
    if not last_time:
        return True
    
    try:
        last_dt = datetime.fromisoformat(last_time)
        hours_passed = (datetime.now() - last_dt).total_seconds() / 3600
        return hours_passed >= cooldown_hours
    except Exception:
        return True


def get_inactive_players(days=7):
    """Получить список неактивных игроков."""
    conn = get_conn()
    try:
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        rows = conn.execute(
            """SELECT user_id, name, last_bonus, last_peer_id 
               FROM players 
               WHERE updated_at < ? AND notify_inactivity = 1""",
            (cutoff,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()