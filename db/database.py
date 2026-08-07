"""
Инициализация и управление базой данных Club Anicoke Bot.
"""
import sqlite3
import logging

logger = logging.getLogger('ClubAnicoke')

def get_connection(db_path):
    """Получение соединения с БД"""
    conn = sqlite3.connect(db_path)
    # Возвращаем строки как словари (доступ по имени колонки: row['balance'])
    conn.row_factory = sqlite3.Row
    # WAL режим для высокой производительности при одновременных запросах
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(conn):
    """Инициализация всех таблиц"""
    cursor = conn.cursor()
    
    # 1. Таблица игроков
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS players (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            balance INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            experience INTEGER DEFAULT 0,
            clan_id INTEGER,
            season_points INTEGER DEFAULT 0,       <-- Добавлено для сезонов
            last_peer_id INTEGER,                  <-- Добавлено для рассылки
            last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            completed_quests INTEGER DEFAULT 0
        )
    """)
    
    # 2. Таблица дуэлей
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS duels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            challenger_id INTEGER,
            opponent_id INTEGER,
            bet INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending', -- pending, active, finished
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 3. Таблица питомцев
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            pet_type TEXT,
            active INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES players(user_id)
        )
    """)
    
    # 4. Таблица текущего босса
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS boss_fights (
            id INTEGER PRIMARY KEY,
            boss_hp INTEGER DEFAULT 10000,
            boss_max_hp INTEGER DEFAULT 10000,
            boss_level INTEGER DEFAULT 1
        )
    """)
    # Создаём запись о боссе, если её ещё нет
    cursor.execute("""
        INSERT OR IGNORE INTO boss_fights (id, boss_hp, boss_max_hp, boss_level) 
        VALUES (1, 10000, 10000, 1)
    """)
    
    # 5. Таблица атак по боссу (история)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS boss_attacks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            damage INTEGER,
            attack_time DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 6. Таблица логов команд (для статистики /статистика)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS command_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            command TEXT,
            used_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    logger.info("✅ База данных успешно инициализирована")