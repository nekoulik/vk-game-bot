"""
База данных для управления предметами.
"""
import sqlite3
import os

# Прямой путь к БД
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "game.db")


def get_conn():
    """Получить соединение с БД напрямую."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_items_table():
    """Инициализировать таблицу предметов."""
    conn = get_conn()
    
    # Проверяем существует ли таблица
    cursor = conn.execute('''
        SELECT name FROM sqlite_master WHERE type='table' AND name='items'
    ''')
    table_exists = cursor.fetchone() is not None
    
    if not table_exists:
        # Создаём таблицу с нуля
        conn.execute('''
            CREATE TABLE items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                item_id TEXT,
                quantity INTEGER DEFAULT 1,
                equipped INTEGER DEFAULT 0,
                acquired_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES players(user_id)
            )
        ''')
        print("✅ Таблица items создана")
    else:
        # Проверяем и добавляем новые колонки если нужно
        cursor = conn.execute('PRAGMA table_info(items)')
        columns = [row[1] for row in cursor.fetchall()]
        
        new_columns = [
            ('equipped', 'INTEGER DEFAULT 0'),
            ('acquired_at', 'DATETIME DEFAULT CURRENT_TIMESTAMP'),
        ]
        
        for col_name, col_type in new_columns:
            if col_name not in columns:
                try:
                    conn.execute(f'ALTER TABLE items ADD COLUMN {col_name} {col_type}')
                    print(f"✅ Добавлена колонка: {col_name}")
                except Exception as e:
                    print(f"⚠️ Не удалось добавить {col_name}: {e}")
    
    conn.commit()
    conn.close()


def get_equipment(user_id):
    """Получить экипировку игрока."""
    conn = get_conn()
    cursor = conn.execute('''
        SELECT item_id FROM items 
        WHERE user_id = ? AND equipped = 1
    ''', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    
    equipment = {'weapon': None, 'armor': None}
    for row in rows:
        item_id = row[0]
        # Определяем тип предмета (упрощённо)
        if 'weapon' in item_id.lower() or 'sword' in item_id.lower() or 'axe' in item_id.lower():
            equipment['weapon'] = item_id
        elif 'armor' in item_id.lower() or 'shield' in item_id.lower():
            equipment['armor'] = item_id
    
    return equipment


def add_item(user_id, item_id, quantity=1):
    """Добавить предмет игроку."""
    conn = get_conn()
    conn.execute('''
        INSERT INTO items (user_id, item_id, quantity)
        VALUES (?, ?, ?)
    ''', (user_id, item_id, quantity))
    conn.commit()
    conn.close()


def get_inventory(user_id):
    """Получить инвентарь игрока."""
    conn = get_conn()
    cursor = conn.execute('''
        SELECT * FROM items WHERE user_id = ?
    ''', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def remove_item(user_id, item_id, quantity=1):
    """Удалить предмет из инвентаря."""
    conn = get_conn()
    try:
        # Получаем текущее количество
        row = conn.execute(
            "SELECT quantity FROM items WHERE player_id = ? AND item_id = ?",
            (user_id, item_id)
        ).fetchone()
        
        if not row:
            return False
        
        current_qty = row["quantity"]
        
        if current_qty <= quantity:
            # Удаляем полностью
            conn.execute(
                "DELETE FROM items WHERE player_id = ? AND item_id = ?",
                (user_id, item_id)
            )
        else:
            # Уменьшаем количество
            conn.execute(
                "UPDATE items SET quantity = quantity - ? WHERE player_id = ? AND item_id = ?",
                (quantity, user_id, item_id)
            )
        
        conn.commit()
        return True
    finally:
        conn.close()