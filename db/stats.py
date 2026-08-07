import sqlite3
from datetime import datetime, timedelta

def get_server_stats(conn):
    """Получить полную статистику сервера"""
    cursor = conn.cursor()
    
    stats = {}
    
    # 1. Общее количество игроков
    cursor.execute("SELECT COUNT(*) FROM players")
    stats['total_players'] = cursor.fetchone()[0]
    
    # 2. Активные игроки сегодня (игравшие за последние 24 часа)
    cursor.execute("""
        SELECT COUNT(DISTINCT user_id) FROM players 
        WHERE last_activity >= datetime('now', '-1 day')
    """)
    stats['active_today'] = cursor.fetchone()[0]
    
    # 3. Активные игроки за неделю
    cursor.execute("""
        SELECT COUNT(DISTINCT user_id) FROM players 
        WHERE last_activity >= datetime('now', '-7 days')
    """)
    stats['active_week'] = cursor.fetchone()[0]
    
    # 4. Общее количество монет в игре
    cursor.execute("SELECT SUM(balance) FROM players")
    stats['total_money'] = cursor.fetchone()[0] or 0
    
    # 5. Средний баланс
    cursor.execute("SELECT AVG(balance) FROM players")
    stats['avg_balance'] = cursor.fetchone()[0] or 0
    
    # 6. Топ-3 богача
    cursor.execute("""
        SELECT username, balance FROM players 
        ORDER BY balance DESC LIMIT 3
    """)
    stats['top_rich'] = cursor.fetchall()
    
    # 7. Количество дуэлей (всего)
    cursor.execute("SELECT COUNT(*) FROM duels")
    stats['total_duels'] = cursor.fetchone()[0]
    
    # 8. Активные дуэли (в процессе)
    cursor.execute("""
        SELECT COUNT(*) FROM duels 
        WHERE status = 'active' OR status = 'pending'
    """)
    stats['active_duels'] = cursor.fetchone()[0]
    
    # 9. Количество квестов выполнено (всего)
    cursor.execute("""
        SELECT SUM(completed_quests) FROM players
    """)
    stats['total_quests'] = cursor.fetchone()[0] or 0
    
    # 10. Количество питомцев
    cursor.execute("SELECT COUNT(*) FROM pets WHERE active = 1")
    stats['active_pets'] = cursor.fetchone()[0]
    
    # 11. Количество кланов
    cursor.execute("SELECT COUNT(DISTINCT clan_id) FROM players WHERE clan_id IS NOT NULL")
    stats['total_clans'] = cursor.fetchone()[0]
    
    # 12. Босс статистика
    cursor.execute("""
        SELECT boss_hp, boss_max_hp, boss_level FROM boss_fights 
        WHERE id = 1
    """)
    boss_data = cursor.fetchone()
    if boss_data:
        stats['boss_hp'] = boss_data[0]
        stats['boss_max_hp'] = boss_data[1]
        stats['boss_level'] = boss_data[2]
    else:
        stats['boss_hp'] = 1000
        stats['boss_max_hp'] = 1000
        stats['boss_level'] = 1
    
    # 13. Количество атак босса сегодня
    cursor.execute("""
        SELECT COUNT(*) FROM boss_attacks 
        WHERE attack_time >= datetime('now', '-1 day')
    """)
    stats['boss_attacks_today'] = cursor.fetchone()[0]
    
    # 14. Новые игроки сегодня
    cursor.execute("""
        SELECT COUNT(*) FROM players 
        WHERE created_at >= datetime('now', '-1 day')
    """)
    stats['new_players_today'] = cursor.fetchone()[0]
    
    # 15. Новые игроки за неделю
    cursor.execute("""
        SELECT COUNT(*) FROM players 
        WHERE created_at >= datetime('now', '-7 days')
    """)
    stats['new_players_week'] = cursor.fetchone()[0]
    
    return stats


def get_command_stats(conn):
    """Статистика использования команд (если ведёшь лог)"""
    cursor = conn.cursor()
    
    # Если есть таблица command_logs
    try:
        cursor.execute("""
            SELECT command, COUNT(*) as count 
            FROM command_logs 
            WHERE used_at >= datetime('now', '-1 day')
            GROUP BY command 
            ORDER BY count DESC 
            LIMIT 5
        """)
        return cursor.fetchall()
    except:
        return []


def get_online_stats(conn):
    """Статистика онлайна за последние 24 часа"""
    cursor = conn.cursor()
    
    # Группировка по часам
    cursor.execute("""
        SELECT 
            strftime('%H', last_activity) as hour,
            COUNT(*) as count
        FROM players 
        WHERE last_activity >= datetime('now', '-1 day')
        GROUP BY hour
        ORDER BY hour
    """)
    return cursor.fetchall()