"""
Функции для работы с базой данных (запросы).
"""
import sqlite3
from datetime import datetime


def get_player(conn, user_id, name_func=None):
    """Получить игрока по ID."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM players WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if row:
        player = dict(row)
        if name_func and not player.get('username'):
            player['name'] = name_func(user_id)
        else:
            player['name'] = player.get('username', f"ID{user_id}")
        return player
    return None


def save_player(conn, player):
    """Сохранить изменения игрока."""
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE players 
        SET balance = ?, level = ?, experience = ?, 
            season_points = ?, last_activity = CURRENT_TIMESTAMP
        WHERE user_id = ?
    """, (
        player['balance'], 
        player['level'], 
        player['experience'],
        player.get('season_points', 0),
        player['user_id']
    ))
    conn.commit()


def get_top_players(conn, limit=10):
    """Получить топ игроков по балансу."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT username, balance, level 
        FROM players 
        WHERE balance != -1 
        ORDER BY balance DESC 
        LIMIT ?
    """, (limit,))
    return [dict(row) for row in cursor.fetchall()]


def add_coins_to_player(conn, user_id, amount):
    """Добавить/списать монеты."""
    cursor = conn.cursor()
    cursor.execute("UPDATE players SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    return cursor.rowcount > 0


def ban_player(conn, user_id):
    """Забанить игрока."""
    cursor = conn.cursor()
    cursor.execute("UPDATE players SET balance = -1 WHERE user_id = ?", (user_id,))
    conn.commit()
    return cursor.rowcount > 0


def unban_player(conn, user_id):
    """Разбанить игрока."""
    cursor = conn.cursor()
    cursor.execute("UPDATE players SET balance = 0 WHERE user_id = ? AND balance = -1", (user_id,))
    conn.commit()
    return cursor.rowcount > 0


def create_duel_challenge(conn, challenger_id, target_id):
    """Создать вызов на дуэль."""
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO duels (challenger_id, opponent_id, bet, status)
        VALUES (?, ?, 50, 'pending')
    """, (challenger_id, target_id))
    conn.commit()
    return cursor.lastrowid


def get_duel_challenge_for_user(conn, user_id):
    """Получить вызов для пользователя."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM duels 
        WHERE opponent_id = ? AND status = 'pending'
        ORDER BY created_at DESC LIMIT 1
    """, (user_id,))
    row = cursor.fetchone()
    return dict(row) if row else None


def get_duel_challenges_for_user(conn, user_id):
    """Получить все вызовы для пользователя."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM duels 
        WHERE opponent_id = ? AND status = 'pending'
    """, (user_id,))
    return [dict(row) for row in cursor.fetchall()]


def clear_duel_challenge(conn, duel_id):
    """Удалить вызов."""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM duels WHERE id = ?", (duel_id,))
    conn.commit()


def start_duel(conn, player1_id, player2_id, stake):
    """Начать дуэль (создать запись)."""
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO duels (challenger_id, opponent_id, bet, status)
        VALUES (?, ?, ?, 'active')
    """, (player1_id, player2_id, stake))
    conn.commit()
    return cursor.lastrowid


def get_active_duel(conn, user_id):
    """Получить активную дуэль игрока."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM duels 
        WHERE (challenger_id = ? OR opponent_id = ?) AND status = 'active'
        LIMIT 1
    """, (user_id, user_id))
    row = cursor.fetchone()
    return dict(row) if row else None


def end_duel(conn, duel_id, winner_id):
    """Завершить дуэль."""
    cursor = conn.cursor()
    cursor.execute("UPDATE duels SET status = 'finished' WHERE id = ?", (duel_id,))
    conn.commit()


def get_stats(conn):
    """Получить общую статистику."""
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM players")
    total_players = cursor.fetchone()[0]
    
    cursor.execute("SELECT COALESCE(SUM(balance), 0) FROM players WHERE balance != -1")
    total_coins = cursor.fetchone()[0]
    
    cursor.execute("SELECT COALESCE(AVG(level), 0) FROM players")
    avg_level = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM duels WHERE status = 'finished'")
    total_duels = cursor.fetchone()[0]
    
    return {
        'total_players': total_players,
        'total_coins': total_coins,
        'avg_level': int(avg_level),
        'total_duels': total_duels,
        'total_boss_kills': 0  # Пока нет таблицы убийств босса
    }


def get_all_players(conn):
    """Получить всех игроков."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM players ORDER BY balance DESC")
    return [dict(row) for row in cursor.fetchall()]


def get_all_peer_ids(conn):
    """Получить все peer_id для рассылки."""
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, last_peer_id FROM players WHERE balance != -1 AND last_peer_id IS NOT NULL")
    return [dict(row) for row in cursor.fetchall()]


def force_reset_season(conn):
    """Сбросить сезон."""
    cursor = conn.cursor()
    cursor.execute("UPDATE players SET season_points = 0")
    conn.commit()
    return cursor.rowcount


def clear_boss(conn):
    """Сбросить босса."""
    cursor = conn.cursor()
    cursor.execute("UPDATE boss_fights SET boss_hp = boss_max_hp WHERE id = 1")
    conn.commit()