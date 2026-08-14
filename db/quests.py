"""
Модуль работы с квестами в базе данных.
"""
import sqlite3
from datetime import datetime, date


def init_quests_table():
    """Инициализировать таблицу квестов."""
    from db import get_conn
    conn = get_conn()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS daily_quests (
            user_id INTEGER,
            quest_key TEXT,
            progress INTEGER DEFAULT 0,
            completed INTEGER DEFAULT 0,
            reward_claimed INTEGER DEFAULT 0,
            date TEXT,
            PRIMARY KEY (user_id, quest_key, date)
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS achievements (
            user_id INTEGER,
            achievement_key TEXT,
            completed INTEGER DEFAULT 0,
            completed_at DATETIME,
            PRIMARY KEY (user_id, achievement_key)
        )
    ''')
    conn.commit()
    conn.close()


def get_daily_quests(user_id):
    """Получить прогресс ежедневных квестов игрока."""
    from db import get_conn
    conn = get_conn()
    today = date.today().isoformat()
    cursor = conn.execute(
        "SELECT quest_key, progress, completed, reward_claimed FROM daily_quests WHERE user_id = ? AND date = ?",
        (user_id, today)
    )
    quests = {row["quest_key"]: dict(row) for row in cursor.fetchall()}
    conn.close()
    return quests


def update_quest_progress(user_id, quest_key, amount=1):
    """Обновить прогресс квеста."""
    from db import get_conn
    conn = get_conn()
    today = date.today().isoformat()
    conn.execute('''
        INSERT INTO daily_quests (user_id, quest_key, progress, date)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id, quest_key, date) DO UPDATE SET progress = progress + ?
    ''', (user_id, quest_key, amount, today, amount))
    conn.commit()
    conn.close()


def claim_quest_reward(user_id, quest_key):
    """Забрать награду за квест."""
    from db import get_conn
    conn = get_conn()
    today = date.today().isoformat()
    cursor = conn.execute(
        "SELECT * FROM daily_quests WHERE user_id = ? AND quest_key = ? AND date = ? AND completed = 1 AND reward_claimed = 0",
        (user_id, quest_key, today)
    )
    quest = cursor.fetchone()
    if not quest:
        conn.close()
        return None, "Квест не выполнен или награда уже получена"
    
    conn.execute(
        "UPDATE daily_quests SET reward_claimed = 1 WHERE user_id = ? AND quest_key = ? AND date = ?",
        (user_id, quest_key, today)
    )
    conn.commit()
    conn.close()
    return dict(quest), None


def get_achievements(user_id):
    """Получить достижения игрока."""
    from db import get_conn
    conn = get_conn()
    cursor = conn.execute(
        "SELECT achievement_key, completed, completed_at FROM achievements WHERE user_id = ?",
        (user_id,)
    )
    achievements = {row["achievement_key"]: dict(row) for row in cursor.fetchall()}
    conn.close()
    return achievements


def unlock_achievement(user_id, achievement_key):
    """Разблокировать достижение."""
    from db import get_conn
    conn = get_conn()
    conn.execute('''
        INSERT OR IGNORE INTO achievements (user_id, achievement_key, completed, completed_at)
        VALUES (?, ?, 1, ?)
    ''', (user_id, achievement_key, datetime.now().isoformat()))
    conn.commit()
    conn.close()