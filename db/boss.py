"""
База данных для управления боссом.
"""
import random
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


def init_boss_table():
    """Инициализировать таблицу босса."""
    conn = get_conn()
    
    cursor = conn.execute('''
        SELECT name FROM sqlite_master WHERE type='table' AND name='boss'
    ''')
    table_exists = cursor.fetchone() is not None
    
    if not table_exists:
        conn.execute('''
            CREATE TABLE boss (
                id INTEGER PRIMARY KEY DEFAULT 1,
                current_hp INTEGER DEFAULT 1000,
                max_hp INTEGER DEFAULT 1000,
                level INTEGER DEFAULT 1,
                is_active INTEGER DEFAULT 0,
                last_spawn DATETIME,
                reward INTEGER DEFAULT 500,
                CHECK (id = 1)
            )
        ''')
        
        conn.execute('''
            INSERT INTO boss (id, current_hp, max_hp, is_active)
            VALUES (1, 1000, 1000, 0)
        ''')
        print("✅ Таблица boss создана")
    else:
        cursor = conn.execute('PRAGMA table_info(boss)')
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'is_active' not in columns:
            conn.execute('ALTER TABLE boss ADD COLUMN is_active INTEGER DEFAULT 0')
        if 'last_spawn' not in columns:
            conn.execute('ALTER TABLE boss ADD COLUMN last_spawn DATETIME')
        if 'reward' not in columns:
            conn.execute('ALTER TABLE boss ADD COLUMN reward INTEGER DEFAULT 500')
        
        cursor = conn.execute('SELECT COUNT(*) FROM boss')
        if cursor.fetchone()[0] == 0:
            conn.execute('''
                INSERT INTO boss (id, current_hp, max_hp, is_active, reward)
                VALUES (1, 1000, 1000, 0, 500)
            ''')
    
    conn.commit()
    conn.close()


def get_boss():
    """Получить данные о боссе."""
    conn = get_conn()
    cursor = conn.execute('SELECT * FROM boss WHERE id = 1')
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)  # ✅ Надёжно
    
    return None


def spawn_boss(level=1):
    """Создать нового босса (сразу активного)."""
    max_hp = 1000 * level
    reward = 500 * level
    
    conn = get_conn()
    
    # Проверяем, существует ли запись
    cursor = conn.execute('SELECT COUNT(*) FROM boss WHERE id = 1')
    exists = cursor.fetchone()[0] > 0
    
    if exists:
        # Обновляем существующую запись и делаем активной
        conn.execute('''
            UPDATE boss SET 
                current_hp = ?,
                max_hp = ?,
                level = ?,
                is_active = 1,
                last_spawn = ?,
                reward = ?
            WHERE id = 1
        ''', (max_hp, max_hp, level, datetime.now().isoformat(), reward))
    else:
        # Создаём новую активную запись
        conn.execute('''
            INSERT INTO boss (id, current_hp, max_hp, level, is_active, last_spawn, reward)
            VALUES (1, ?, ?, ?, 1, ?, ?)
        ''', (max_hp, max_hp, level, datetime.now().isoformat(), reward))
    
    conn.commit()
    conn.close()


def attack_boss(user_id, damage):
    """
    Атаковать босса.
    Возвращает: (нанесённый урон, убит ли босс, награда)
    """
    boss = get_boss()
    
    if not boss or not boss['is_active']:
        return 0, False, 0
    
    new_hp = boss['current_hp'] - damage
    if new_hp < 0:
        new_hp = 0
    
    conn = get_conn()
    conn.execute('UPDATE boss SET current_hp = ? WHERE id = 1', (new_hp,))
    
    boss_killed = False
    reward = 0
    
    if new_hp == 0:
        reward = boss['reward']
        conn.execute('UPDATE boss SET is_active = 0 WHERE id = 1')
        boss_killed = True
    
    conn.commit()
    conn.close()
    
    return damage, boss_killed, reward


def get_boss_damage(user_id):
    """Рассчитать урон игрока по боссу."""
    conn = get_conn()
    cursor = conn.execute('SELECT level FROM players WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        level = row[0]
    else:
        level = 1
    
    base_damage = level * 10
    variance = random.uniform(0.8, 1.2)
    final_damage = int(base_damage * variance)
    
    return max(final_damage, 5)


def get_boss_cooldown():
    """Проверить можно ли заспавнить босса (кулдаун 6 часов)."""
    boss = get_boss()
    
    if not boss:
        return True
    
    if not boss.get('last_spawn'):
        return True
    
    last_spawn = datetime.fromisoformat(boss['last_spawn'])
    now = datetime.now()
    hours_passed = (now - last_spawn).total_seconds() / 3600
    
    return hours_passed >= 6


def clear_boss():
    """Удалить текущего босса."""
    conn = get_conn()
    conn.execute('DELETE FROM boss WHERE id = 1')
    conn.commit()
    changes = conn.total_changes
    conn.close()
    return changes > 0