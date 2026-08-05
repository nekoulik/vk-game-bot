"""Функции для работы с дуэлями."""
from db.base import get_conn


def get_duel(challenged_id):
    """Получить активную дуэль."""
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM duels WHERE challenged_id = ?", (challenged_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def save_duel(challenged_id, challenger_id, challenger_peer_id, timestamp):
    """Сохранить дуэль."""
    conn = get_conn()
    try:
        conn.execute("INSERT OR REPLACE INTO duels (challenged_id, challenger_id, challenger_peer_id, timestamp) VALUES (?, ?, ?, ?)",
                     (challenged_id, challenger_id, challenger_peer_id, timestamp))
        conn.commit()
    finally:
        conn.close()


def delete_duel(challenged_id):
    """Удалить дуэль."""
    conn = get_conn()
    try:
        conn.execute("DELETE FROM duels WHERE challenged_id = ?", (challenged_id,))
        conn.commit()
    finally:
        conn.close()