"""
База данных для управления дуэлями.
"""
import random
from db.base import get_conn
from datetime import datetime, timedelta


def init_duels_table():
    """Инициализировать таблицы дуэлей."""
    conn = get_conn()
    try:
        # Таблица старых дуэлей
        conn.execute('''
            CREATE TABLE IF NOT EXISTS duels (
                challenged_id INTEGER PRIMARY KEY,
                challenger_id INTEGER,
                challenger_peer_id INTEGER,
                timestamp REAL
            )
        ''')
        
        # Таблица вызовов на дуэль
        conn.execute('''
            CREATE TABLE IF NOT EXISTS duel_challenges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                challenger_id INTEGER,
                target_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица активных дуэлей
        conn.execute('''
            CREATE TABLE IF NOT EXISTS active_duels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player1_id INTEGER,
                player2_id INTEGER,
                stake INTEGER DEFAULT 50,
                status TEXT DEFAULT 'active',
                winner_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                finished_at DATETIME
            )
        ''')
        
        # Таблица PvP-вызовов
        conn.execute('''
            CREATE TABLE IF NOT EXISTS pvp_challenges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                challenger_id INTEGER,
                target_id INTEGER,
                stake INTEGER DEFAULT 50,
                status TEXT DEFAULT 'pending',
                winner_id INTEGER,
                challenger_roll INTEGER,
                target_roll INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                accepted_at DATETIME,
                finished_at DATETIME,
                FOREIGN KEY (challenger_id) REFERENCES players(user_id),
                FOREIGN KEY (target_id) REFERENCES players(user_id)
            )
        ''')
        
        conn.commit()
        print("✅ Таблицы дуэлей созданы")
    finally:
        conn.close()


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


def start_duel(player1_id, player2_id, stake=50):
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
    """Завершить дуэль."""
    conn = get_conn()
    try:
        conn.execute(
            "UPDATE active_duels SET status = 'finished', winner_id = ?, finished_at = ? WHERE id = ?",
            (winner_id, datetime.now().isoformat(), duel_id)
        )
        conn.commit()
    finally:
        conn.close()


# === PvP ФУНКЦИИ ===

def clear_old_pvp_challenges():
    """Очистить старые pending вызовы (старше 1 часа)."""
    conn = get_conn()
    try:
        one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()
        conn.execute(
            "DELETE FROM pvp_challenges WHERE status = 'pending' AND created_at < ?",
            (one_hour_ago,)
        )
        conn.commit()
    finally:
        conn.close()


def create_pvp_challenge(challenger_id, target_id, stake):
    """Создать PvP-вызов."""
    conn = get_conn()
    try:
        # ✅ Сначала очищаем старые вызовы (старше 1 часа)
        one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()
        conn.execute(
            "DELETE FROM pvp_challenges WHERE status = 'pending' AND created_at < ?",
            (one_hour_ago,)
        )
        conn.commit()
        
        # Проверяем, нет ли уже активного вызова у challenger
        existing = conn.execute(
            "SELECT id FROM pvp_challenges WHERE (challenger_id = ? OR target_id = ?) AND status = 'pending'",
            (challenger_id, challenger_id)
        ).fetchone()
        
        if existing:
            return None, "У тебя уже есть активный вызов! Напиши *отменить* чтобы отменить его."
        
        # Проверяем, нет ли уже активного вызова у target
        existing = conn.execute(
            "SELECT id FROM pvp_challenges WHERE (challenger_id = ? OR target_id = ?) AND status = 'pending'",
            (target_id, target_id)
        ).fetchone()
        
        if existing:
            return None, "У этого игрока уже есть активный вызов!"
        
        now = datetime.now().isoformat()
        cursor = conn.execute(
            """INSERT INTO pvp_challenges 
               (challenger_id, target_id, stake, status, created_at) 
               VALUES (?, ?, ?, 'pending', ?)""",
            (challenger_id, target_id, stake, now)
        )
        challenge_id = cursor.lastrowid
        conn.commit()
        return challenge_id, None
    finally:
        conn.close()


def get_pvp_challenge_for_user(user_id):
    """Получить входящий PvP-вызов для пользователя."""
    conn = get_conn()
    try:
        row = conn.execute(
            """SELECT * FROM pvp_challenges 
               WHERE target_id = ? AND status = 'pending'
               ORDER BY created_at DESC LIMIT 1""",
            (user_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_pvp_outgoing_challenge(user_id):
    """Получить исходящий PvP-вызов пользователя."""
    conn = get_conn()
    try:
        row = conn.execute(
            """SELECT * FROM pvp_challenges 
               WHERE challenger_id = ? AND status = 'pending'
               ORDER BY created_at DESC LIMIT 1""",
            (user_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def cancel_pvp_challenge(user_id):
    """Отменить свой исходящий PvP-вызов."""
    conn = get_conn()
    try:
        challenge = conn.execute(
            "SELECT * FROM pvp_challenges WHERE challenger_id = ? AND status = 'pending'",
            (user_id,)
        ).fetchone()
        
        if not challenge:
            return False, "У тебя нет активных вызовов!"
        
        conn.execute(
            "DELETE FROM pvp_challenges WHERE id = ?",
            (challenge["id"],)
        )
        conn.commit()
        return True, None
    finally:
        conn.close()


def accept_pvp_challenge(challenge_id, target_id):
    """Принять PvP-вызов."""
    conn = get_conn()
    try:
        challenge = conn.execute(
            "SELECT * FROM pvp_challenges WHERE id = ? AND target_id = ? AND status = 'pending'",
            (challenge_id, target_id)
        ).fetchone()
        
        if not challenge:
            return None, "Вызов не найден или уже принят!"
        
        conn.execute(
            "UPDATE pvp_challenges SET status = 'accepted', accepted_at = ? WHERE id = ?",
            (datetime.now().isoformat(), challenge_id)
        )
        conn.commit()
        return dict(challenge), None
    finally:
        conn.close()


def start_pvp_battle(challenge_id):
    """Начать PvP-бой."""
    conn = get_conn()
    try:
        challenge = conn.execute(
            "SELECT * FROM pvp_challenges WHERE id = ? AND status = 'accepted'",
            (challenge_id,)
        ).fetchone()
        
        if not challenge:
            return None, "Бой не может начаться!"
        
        challenge = dict(challenge)
        
        # Генерируем броски
        challenger_roll = random.randint(1, 100)
        target_roll = random.randint(1, 100)
        
        # Определяем победителя
        if challenger_roll > target_roll:
            winner_id = challenge["challenger_id"]
            loser_id = challenge["target_id"]
        elif target_roll > challenger_roll:
            winner_id = challenge["target_id"]
            loser_id = challenge["challenger_id"]
        else:
            winner_id = None  # Ничья
        
        # Обновляем баланс
        stake = challenge["stake"]
        if winner_id:
            conn.execute(
                "UPDATE players SET balance = balance + ? WHERE user_id = ?",
                (stake * 2, winner_id)
            )
            conn.execute(
                "UPDATE players SET balance = balance - ? WHERE user_id = ?",
                (stake, loser_id)
            )
        else:
            # Ничья — возвращаем ставки обоим
            conn.execute(
                "UPDATE players SET balance = balance + ? WHERE user_id = ?",
                (stake, challenge["challenger_id"])
            )
            conn.execute(
                "UPDATE players SET balance = balance + ? WHERE user_id = ?",
                (stake, challenge["target_id"])
            )
        
        # Завершаем вызов
        conn.execute(
            """UPDATE pvp_challenges 
               SET status = 'finished', winner_id = ?, 
                   challenger_roll = ?, target_roll = ?,
                   finished_at = ?
               WHERE id = ?""",
            (winner_id, challenger_roll, target_roll, datetime.now().isoformat(), challenge_id)
        )
        conn.commit()
        
        return {
            "challenge": challenge,
            "challenger_roll": challenger_roll,
            "target_roll": target_roll,
            "winner_id": winner_id
        }, None
    finally:
        conn.close()


def decline_pvp_challenge(challenge_id, user_id):
    """Отклонить PvP-вызов."""
    conn = get_conn()
    try:
        conn.execute(
            "UPDATE pvp_challenges SET status = 'declined' WHERE id = ? AND target_id = ?",
            (challenge_id, user_id)
        )
        conn.commit()
        return True
    finally:
        conn.close()


def get_pvp_accepted_challenge(user_id):
    """Получить принятый PvP-вызов для пользователя (для начала боя)."""
    conn = get_conn()
    try:
        row = conn.execute(
            """SELECT * FROM pvp_challenges 
               WHERE (challenger_id = ? OR target_id = ?) AND status = 'accepted'
               ORDER BY accepted_at DESC LIMIT 1""",
            (user_id, user_id)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()