"""Настройки беседы: ограничения, приветствия, уведомления."""
from db.base import get_conn


def init_chat_settings_table():
    """Создать таблицу настроек беседы."""
    conn = get_conn()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_settings (
                peer_id INTEGER PRIMARY KEY,
                is_restricted INTEGER DEFAULT 0,
                welcome_message TEXT DEFAULT '',
                goodbye_message TEXT DEFAULT '',
                notify_join INTEGER DEFAULT 1,
                notify_leave INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    finally:
        conn.close()


def get_chat_settings(peer_id):
    """Получить настройки беседы."""
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT * FROM chat_settings WHERE peer_id = ?", (peer_id,)
        ).fetchone()
        if row:
            return dict(row)
        # Создаём настройки по умолчанию
        conn.execute(
            "INSERT INTO chat_settings (peer_id) VALUES (?)", (peer_id,)
        )
        conn.commit()
        return dict(conn.execute(
            "SELECT * FROM chat_settings WHERE peer_id = ?", (peer_id,)
        ).fetchone())
    finally:
        conn.close()


def set_chat_restricted(peer_id, is_restricted):
    """Включить/выключить ограничение входа."""
    conn = get_conn()
    try:
        conn.execute(
            "UPDATE chat_settings SET is_restricted = ? WHERE peer_id = ?",
            (is_restricted, peer_id)
        )
        conn.commit()
    finally:
        conn.close()


def set_welcome_message(peer_id, message):
    """Установить приветственное сообщение."""
    conn = get_conn()
    try:
        conn.execute(
            "UPDATE chat_settings SET welcome_message = ? WHERE peer_id = ?",
            (message, peer_id)
        )
        conn.commit()
    finally:
        conn.close()


def set_goodbye_message(peer_id, message):
    """Установить прощальное сообщение."""
    conn = get_conn()
    try:
        conn.execute(
            "UPDATE chat_settings SET goodbye_message = ? WHERE peer_id = ?",
            (message, peer_id)
        )
        conn.commit()
    finally:
        conn.close()


def set_notify_join(peer_id, enabled):
    """Включить/выключить уведомления о входе."""
    conn = get_conn()
    try:
        conn.execute(
            "UPDATE chat_settings SET notify_join = ? WHERE peer_id = ?",
            (enabled, peer_id)
        )
        conn.commit()
    finally:
        conn.close()


def set_notify_leave(peer_id, enabled):
    """Включить/выключить уведомления о выходе."""
    conn = get_conn()
    try:
        conn.execute(
            "UPDATE chat_settings SET notify_leave = ? WHERE peer_id = ?",
            (enabled, peer_id)
        )
        conn.commit()
    finally:
        conn.close()


def kick_user(api, peer_id, user_id):
    """Выгнать пользователя из беседы."""
    try:
        api.messages.removeChatUser(chat_id=peer_id - 2000000000, user_id=user_id)
        return True
    except Exception as e:
        print(f"Ошибка при выгонении {user_id}: {e}")
        return False