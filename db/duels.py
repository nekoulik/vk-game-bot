from db.base import get_conn
from datetime import datetime


def get_duel(user_id):
    """Получить дуэль пользователя (старая система)."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM duels WHERE challenged_id = ?", (user_id,)
        ).fetchone()
        return dict(row) if row else None


def save_duel(challenged_id, challenger_id, challenger_peer_id, timestamp=None):
    """Сохранить дуэль (старая система)."""
    if timestamp is None:
        timestamp = datetime.now().timestamp()
    conn = get_conn()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO duels (challenged_id, challenger_id, challenger_peer_id, timestamp) VALUES (?, ?, ?, ?)",
            (challenged_id, challenger_id, challenger_peer_id, timestamp)
        )
        conn.commit()
    finally:
        conn.close()


def delete_duel(user_id):
    """Удалить дуэль (старая система)."""
    conn = get_conn()
    try:
        conn.execute("DELETE FROM duels WHERE challenged_id = ?", (user_id,))
        conn.commit()
    finally:
        conn.close()


def create_duel_challenge(challenger_id, target_id):
    """Создать вызов на дуэль."""
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO duel_challenges (challenger_id, target_id, created_at) VALUES (?, ?, ?)",
            (challenger_id, target_id, datetime.now().isoformat())
        )
        conn.commit()
    finally:
        conn.close()


def get_duel_challenge_for_user(user_id):
    """Получить активный вызов для пользователя."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM duel_challenges WHERE target_id = ? ORDER BY created_at DESC LIMIT 1",
            (user_id,)
        ).fetchone()
        return dict(row) if row else None


def get_duel_challenges_for_user(user_id):
    """Получить все активные вызовы для пользователя."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM duel_challenges WHERE target_id = ? ORDER BY created_at DESC",
            (user_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def clear_duel_challenge(challenge_id):
    """Удалить вызов."""
    conn = get_conn()
    try:
        conn.execute("DELETE FROM duel_challenges WHERE id = ?", (challenge_id,))
        conn.commit()
    finally:
        conn.close()


def start_duel(player1_id, player2_id, stake):
    """Начать дуэль."""
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO active_duels (player1_id, player2_id, stake, status, created_at) VALUES (?, ?, ?, 'active', ?)",
            (player1_id, player2_id, stake, datetime.now().isoformat())
        )
        conn.commit()
    finally:
        conn.close()


def get_active_duel(user_id):
    """Получить активную дуэль для пользователя."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM active_duels WHERE (player1_id = ? OR player2_id = ?) AND status = 'active'",
            (user_id, user_id)
        ).fetchone()
        return dict(row) if row else None


def end_duel(duel_id, winner_id):
    """Завершить дуэль — меняем статус на 'finished'."""
    conn = get_conn()
    try:
        conn.execute(
            "UPDATE active_duels SET status = 'finished', winner_id = ?, finished_at = ? WHERE id = ?",
            (winner_id, datetime.now().isoformat(), duel_id)
        )
        conn.commit()  # ← ВАЖНО! Сохраняем изменения
    finally:
        conn.close()