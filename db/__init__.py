"""
Пакет базы данных для Club Anicoke Bot.
Инициализирует все таблицы и предоставляет общий доступ к соединению.
"""
import os
import sqlite3
from datetime import datetime

# Путь к базе данных
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "game.db")


def get_conn():
    """Получить соединение с базой данных."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Инициализировать все таблицы базы данных."""
    from db import players, items, duels, quests, clans, boss
    
    # Инициализируем все таблицы
    players.init_players_table()
    items.init_items_table()
    duels.init_duels_table()
    quests.init_quests_table()
    clans.init_clans_table()
    boss.init_boss_table()
    
    print("✅ Все таблицы базы данных инициализированы!")


def init_chat_settings_table():
    """Инициализировать таблицу настроек беседы."""
    conn = get_conn()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS chat_settings (
            peer_id INTEGER PRIMARY KEY,
            is_restricted INTEGER DEFAULT 0,
            welcome_message TEXT DEFAULT '',
            goodbye_message TEXT DEFAULT '',
            notify_join INTEGER DEFAULT 1,
            notify_leave INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


def get_chat_settings(peer_id):
    """Получить настройки беседы."""
    conn = get_conn()
    cursor = conn.execute(
        "SELECT * FROM chat_settings WHERE peer_id = ?",
        (peer_id,)
    )
    row = cursor.fetchone()
    
    if row:
        settings = dict(row)
    else:
        # Создаём настройки по умолчанию
        conn.execute(
            "INSERT INTO chat_settings (peer_id) VALUES (?)",
            (peer_id,)
        )
        conn.commit()
        settings = {
            "peer_id": peer_id,
            "is_restricted": 0,
            "welcome_message": "",
            "goodbye_message": "",
            "notify_join": 1,
            "notify_leave": 1,
            "created_at": datetime.now().isoformat()
        }
    
    conn.close()
    return settings


def set_chat_restricted(peer_id, is_restricted):
    """Установить ограничение беседы."""
    conn = get_conn()
    conn.execute(
        "UPDATE chat_settings SET is_restricted = ? WHERE peer_id = ?",
        (is_restricted, peer_id)
    )
    conn.commit()
    conn.close()


def set_welcome_message(peer_id, message):
    """Установить приветственное сообщение."""
    conn = get_conn()
    conn.execute(
        "UPDATE chat_settings SET welcome_message = ? WHERE peer_id = ?",
        (message, peer_id)
    )
    conn.commit()
    conn.close()


def set_goodbye_message(peer_id, message):
    """Установить прощальное сообщение."""
    conn = get_conn()
    conn.execute(
        "UPDATE chat_settings SET goodbye_message = ? WHERE peer_id = ?",
        (message, peer_id)
    )
    conn.commit()
    conn.close()


def set_notify_join(peer_id, enabled):
    """Установить уведомление о входе."""
    conn = get_conn()
    conn.execute(
        "UPDATE chat_settings SET notify_join = ? WHERE peer_id = ?",
        (enabled, peer_id)
    )
    conn.commit()
    conn.close()


def set_notify_leave(peer_id, enabled):
    """Установить уведомление о выходе."""
    conn = get_conn()
    conn.execute(
        "UPDATE chat_settings SET notify_leave = ? WHERE peer_id = ?",
        (enabled, peer_id)
    )
    conn.commit()
    conn.close()


def kick_user(api, peer_id, user_id):
    """Выгнать пользователя из беседы."""
    try:
        chat_id = peer_id - 2000000000
        api.messages.removeChatUser(chat_id=chat_id, user_id=user_id)
        return True
    except Exception as e:
        print(f"Ошибка выгона пользователя: {e}")
        return False


def get_stats():
    """Получить статистику бота."""
    conn = get_conn()
    
    # Всего игроков
    cursor = conn.execute('SELECT COUNT(*) FROM players')
    total_players = cursor.fetchone()[0]
    
    # Всего монет
    cursor = conn.execute('SELECT SUM(balance) FROM players WHERE balance > 0')
    total_coins = cursor.fetchone()[0] or 0
    
    # Средний уровень
    cursor = conn.execute('SELECT AVG(level) FROM players')
    avg_level = round(cursor.fetchone()[0] or 0, 1)
    
    # Всего дуэлей выиграно
    cursor = conn.execute('SELECT SUM(total_duels_won) FROM players')
    total_duels = cursor.fetchone()[0] or 0
    
    # Всего боссов убито
    cursor = conn.execute('SELECT SUM(total_boss_kills) FROM players')
    total_boss_kills = cursor.fetchone()[0] or 0
    
    conn.close()
    
    return {
        'total_players': total_players,
        'total_coins': int(total_coins),
        'avg_level': avg_level,
        'total_duels': total_duels,
        'total_boss_kills': total_boss_kills
    }


def force_reset_season():
    """Принудительно сбросить очки сезона всем игрокам."""
    conn = get_conn()
    conn.execute('UPDATE players SET season_points = 0')
    conn.execute('UPDATE players SET current_season = current_season + 1')
    conn.commit()
    changes = conn.total_changes
    conn.close()
    return changes


# Импорт всех модулей
from db import players, items, duels, quests, clans, boss

# Экспорт основных функций из players для удобства
from db.players import (
    get_player,
    save_player,
    get_all_players,
    get_top_players,
    add_coins_to_player,
    ban_player,
    unban_player,
    get_all_peer_ids
)

# ✅ Экспорт функций из boss для удобства
from db.boss import (
    get_boss,
    spawn_boss,
    attack_boss,
    clear_boss,
    get_boss_cooldown
)