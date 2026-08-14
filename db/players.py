"""
База данных для управления игроками.
"""
import sqlite3
from datetime import datetime
import os

# Прямой путь к БД
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "game.db")


def get_conn():
    """Получить соединение с БД напрямую."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_players_table():
    """Инициализировать таблицу игроков."""
    conn = get_conn()
    
    cursor = conn.execute('''
        SELECT name FROM sqlite_master WHERE type='table' AND name='players'
    ''')
    table_exists = cursor.fetchone() is not None
    
    if not table_exists:
        conn.execute('''
            CREATE TABLE players (
                user_id INTEGER PRIMARY KEY,
                name TEXT DEFAULT 'Игрок',
                balance INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                exp INTEGER DEFAULT 0,
                last_work INTEGER DEFAULT 0,
                last_bonus TEXT DEFAULT '',
                bonus_streak INTEGER DEFAULT 0,
                last_peer_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                daily_duels INTEGER DEFAULT 0,
                daily_boss_kills INTEGER DEFAULT 0,
                daily_coins_earned INTEGER DEFAULT 0,
                last_quest_date TEXT DEFAULT '',
                total_duels_won INTEGER DEFAULT 0,
                total_boss_kills INTEGER DEFAULT 0,
                daily_quest_claimed INTEGER DEFAULT 0,
                active_pet_id INTEGER,
                season_points INTEGER DEFAULT 0,
                title TEXT DEFAULT '',
                current_season INTEGER DEFAULT 1,
                last_lottery TEXT DEFAULT '',
                notify_bonus INTEGER DEFAULT 1,
                notify_quests INTEGER DEFAULT 1,
                notify_inactivity INTEGER DEFAULT 1,
                mute_until INTEGER DEFAULT 0,
                last_activity DATETIME,
                daily_work INTEGER DEFAULT 0,
                daily_boss_damage INTEGER DEFAULT 0,
                daily_bonus INTEGER DEFAULT 0,
                daily_games INTEGER DEFAULT 0,
                equipped_weapon TEXT,
                active_pet TEXT,
                pet_bonus_coins REAL DEFAULT 0,
                pet_bonus_damage REAL DEFAULT 0
            )
        ''')
        print("✅ Таблица players создана")
    else:
        cursor = conn.execute('PRAGMA table_info(players)')
        columns = [row[1] for row in cursor.fetchall()]
        
        new_columns = [
            ('last_peer_id', 'INTEGER'),
            ('last_activity', 'DATETIME'),
            ('mute_until', 'INTEGER DEFAULT 0'),
            ('daily_duels', 'INTEGER DEFAULT 0'),
            ('daily_boss_kills', 'INTEGER DEFAULT 0'),
            ('daily_coins_earned', 'INTEGER DEFAULT 0'),
            ('last_quest_date', 'TEXT DEFAULT ""'),
            ('total_duels_won', 'INTEGER DEFAULT 0'),
            ('total_boss_kills', 'INTEGER DEFAULT 0'),
            ('daily_quest_claimed', 'INTEGER DEFAULT 0'),
            ('active_pet_id', 'INTEGER'),
            ('season_points', 'INTEGER DEFAULT 0'),
            ('title', 'TEXT DEFAULT ""'),
            ('current_season', 'INTEGER DEFAULT 1'),
            ('last_lottery', 'TEXT DEFAULT ""'),
            ('notify_bonus', 'INTEGER DEFAULT 1'),
            ('notify_quests', 'INTEGER DEFAULT 1'),
            ('notify_inactivity', 'INTEGER DEFAULT 1'),
            ('daily_work', 'INTEGER DEFAULT 0'),
            ('daily_boss_damage', 'INTEGER DEFAULT 0'),
            ('daily_bonus', 'INTEGER DEFAULT 0'),
            ('daily_games', 'INTEGER DEFAULT 0'),
            ('equipped_weapon', 'TEXT'),
            ('active_pet', 'TEXT'),
            ('pet_bonus_coins', 'REAL DEFAULT 0'),
            ('pet_bonus_damage', 'REAL DEFAULT 0'),
        ]
        
        for col_name, col_type in new_columns:
            if col_name not in columns:
                try:
                    conn.execute(f'ALTER TABLE players ADD COLUMN {col_name} {col_type}')
                    print(f"✅ Добавлена колонка: {col_name}")
                except Exception as e:
                    print(f"⚠️ Не удалось добавить {col_name}: {e}")
    
    conn.commit()
    conn.close()


def get_player(user_id, name_callback):
    """Получить или создать игрока."""
    conn = get_conn()
    cursor = conn.execute('SELECT * FROM players WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    
    if row:
        player = dict(row)
        conn.close()
        return player
    
    name = name_callback(user_id)
    conn.execute('''
        INSERT INTO players (user_id, name, created_at)
        VALUES (?, ?, ?)
    ''', (user_id, name, datetime.now().isoformat()))
    conn.commit()
    
    cursor = conn.execute('SELECT * FROM players WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None


def save_player(player):
    """Сохранить данные игрока."""
    conn = get_conn()
    conn.execute('''
        UPDATE players SET
            name = ?,
            balance = ?,
            level = ?,
            exp = ?,
            last_work = ?,
            last_bonus = ?,
            bonus_streak = ?,
            last_peer_id = ?,
            updated_at = ?,
            daily_duels = ?,
            daily_boss_kills = ?,
            daily_coins_earned = ?,
            last_quest_date = ?,
            total_duels_won = ?,
            total_boss_kills = ?,
            daily_quest_claimed = ?,
            active_pet_id = ?,
            season_points = ?,
            title = ?,
            current_season = ?,
            last_lottery = ?,
            notify_bonus = ?,
            notify_quests = ?,
            notify_inactivity = ?,
            mute_until = ?,
            last_activity = ?,
            daily_work = ?,
            daily_boss_damage = ?,
            daily_bonus = ?,
            daily_games = ?,
            equipped_weapon = ?,
            active_pet = ?,
            pet_bonus_coins = ?,
            pet_bonus_damage = ?
        WHERE user_id = ?
    ''', (
        player.get('name', 'Игрок'),
        int(player.get('balance', 0)),
        int(player.get('level', 1)),
        int(player.get('exp', 0)),
        player.get('last_work', 0),
        player.get('last_bonus', ''),
        int(player.get('bonus_streak', 0)),
        player.get('last_peer_id'),
        datetime.now().isoformat(),
        player.get('daily_duels', 0),
        player.get('daily_boss_kills', 0),
        player.get('daily_coins_earned', 0),
        player.get('last_quest_date', ''),
        player.get('total_duels_won', 0),
        player.get('total_boss_kills', 0),
        player.get('daily_quest_claimed', 0),
        player.get('active_pet_id'),
        player.get('season_points', 0),
        player.get('title', ''),
        player.get('current_season', 1),
        player.get('last_lottery', ''),
        player.get('notify_bonus', 1),
        player.get('notify_quests', 1),
        player.get('notify_inactivity', 1),
        player.get('mute_until', 0),
        player.get('last_activity', ''),
        player.get('daily_work', 0),
        player.get('daily_boss_damage', 0),
        player.get('daily_bonus', 0),
        player.get('daily_games', 0),
        player.get('equipped_weapon'),
        player.get('active_pet'),
        player.get('pet_bonus_coins', 0),
        player.get('pet_bonus_damage', 0),
        player['user_id']
    ))
    conn.commit()
    conn.close()


def get_all_players():
    """Получить всех игроков."""
    conn = get_conn()
    cursor = conn.execute('SELECT * FROM players ORDER BY balance DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_top_players(limit=10):
    """Получить топ игроков по балансу."""
    conn = get_conn()
    cursor = conn.execute('SELECT * FROM players ORDER BY balance DESC LIMIT ?', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def add_coins_to_player(user_id, amount):
    """Добавить монеты игроку."""
    conn = get_conn()
    conn.execute('''
        UPDATE players SET balance = balance + ? WHERE user_id = ?
    ''', (amount, user_id))
    conn.commit()
    conn.close()
    return True


def ban_player(user_id):
    """Забанить игрока."""
    conn = get_conn()
    conn.execute('''
        UPDATE players SET balance = -1 WHERE user_id = ?
    ''', (user_id,))
    conn.commit()
    changes = conn.total_changes
    conn.close()
    return changes > 0


def unban_player(user_id):
    """Разбанить игрока."""
    conn = get_conn()
    conn.execute('''
        UPDATE players SET balance = 0 WHERE user_id = ? AND balance = -1
    ''', (user_id,))
    conn.commit()
    changes = conn.total_changes
    conn.close()
    return changes > 0


def get_all_peer_ids():
    """Получить все peer_id игроков."""
    conn = get_conn()
    cursor = conn.execute('SELECT user_id, last_peer_id FROM players WHERE last_peer_id IS NOT NULL')
    rows = cursor.fetchall()
    conn.close()
    return [{'user_id': row[0], 'last_peer_id': row[1]} for row in rows]


def check_and_reset_daily_quests(player):
    """Проверить и сбросить ежедневные квесты если новый день."""
    today = datetime.now().strftime("%Y-%m-%d")
    last_quest_date = player.get("last_quest_date")
    
    if last_quest_date != today:
        player["daily_work"] = 0
        player["daily_duels"] = 0
        player["daily_boss_damage"] = 0
        player["daily_bonus"] = 0
        player["daily_games"] = 0
        player["daily_quest_claimed"] = 0
        player["last_quest_date"] = today
        save_player(player)
    
    return player


def increment_daily_stat(user_id, stat_name, amount=1):
    """Увеличить счётчик ежедневной статистики."""
    player = get_player(user_id, lambda uid: f"Игрок {uid}")
    
    if stat_name == "work":
        player["daily_work"] = player.get("daily_work", 0) + amount
    elif stat_name == "duels_won":
        player["daily_duels"] = player.get("daily_duels", 0) + amount
    elif stat_name == "boss_damage":
        player["daily_boss_damage"] = player.get("daily_boss_damage", 0) + amount
    elif stat_name == "bonus":
        player["daily_bonus"] = player.get("daily_bonus", 0) + amount
    elif stat_name == "games_played":
        player["daily_games"] = player.get("daily_games", 0) + amount
    
    save_player(player)
    return player