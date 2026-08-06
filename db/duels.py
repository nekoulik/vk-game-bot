"""Работа с дуэлями."""
from db.base import get_conn
from datetime import datetime


# ============ СТАРЫЕ ФУНКЦИИ (вызовы) ============

def get_duel(user_id):
    """Получить дуэль пользователя."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM duels WHERE challenged_id = ?", (user_id,)
        ).fetchone()
        return dict(row) if row else None


def save_duel(challenged_id, challenger_id, challenger_peer_id, timestamp=None):
    """Сохранить дуэль."""
    if timestamp is None:
        timestamp = datetime.now().timestamp()
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO duels (challenged_id, challenger_id, challenger_peer_id, timestamp) VALUES (?, ?, ?, ?)",
            (challenged_id, challenger_id, challenger_peer_id, timestamp)
        )


def delete_duel(user_id):
    """Удалить дуэль."""
    with get_conn() as conn:
        conn.execute("DELETE FROM duels WHERE challenged_id = ?", (user_id,))


# ============ НОВЫЕ PvP ФУНКЦИИ ============

def create_duel_challenge(challenger_id, target_id):
    """Создать вызов на дуэль."""
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO duel_challenges (challenger_id, target_id, created_at) VALUES (?, ?, ?)",
            (challenger_id, target_id, datetime.now().isoformat())
        )


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
    with get_conn() as conn:
        conn.execute("DELETE FROM duel_challenges WHERE id = ?", (challenge_id,))


def start_duel(player1_id, player2_id, stake):
    """Начать дуэль."""
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO active_duels (player1_id, player2_id, stake, status, created_at) VALUES (?, ?, ?, 'active', ?)",
            (player1_id, player2_id, stake, datetime.now().isoformat())
        )


def get_active_duel(user_id):
    """Получить активную дуэль для пользователя."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM active_duels WHERE (player1_id = ? OR player2_id = ?) AND status = 'active'",
            (user_id, user_id)
        ).fetchone()
        return dict(row) if row else None


def end_duel(duel_id, winner_id):
    """Завершить дуэль."""
    with get_conn() as conn:
        conn.execute(
            "UPDATE active_duels SET status = 'finished', winner_id = ?, finished_at = ? WHERE id = ?",
            (winner_id, datetime.now().isoformat(), duel_id)
        )