"""Функции для работы с инвентарем и экипировкой."""
from db.base import get_conn


def get_inventory(user_id):
    """Получить инвентарь игрока."""
    conn = get_conn()
    try:
        rows = conn.execute("SELECT item_id, quantity FROM inventory WHERE player_id = ?", (user_id,)).fetchall()
        return {row["item_id"]: row["quantity"] for row in rows}
    finally:
        conn.close()


def add_to_inventory(user_id, item_id, quantity=1):
    """Добавить предмет в инвентарь."""
    conn = get_conn()
    try:
        conn.execute("""INSERT INTO inventory (player_id, item_id, quantity) VALUES (?, ?, ?)
                        ON CONFLICT(player_id, item_id) DO UPDATE SET quantity = quantity + excluded.quantity""", (user_id, item_id, quantity))
        conn.commit()
    finally:
        conn.close()


def remove_from_inventory(user_id, item_id, quantity=1):
    """Удалить предмет из инвентаря."""
    conn = get_conn()
    try:
        row = conn.execute("SELECT quantity FROM inventory WHERE player_id = ? AND item_id = ?", (user_id, item_id)).fetchone()
        if row is None:
            return False
        if row["quantity"] <= quantity:
            conn.execute("DELETE FROM inventory WHERE player_id = ? AND item_id = ?", (user_id, item_id))
        else:
            conn.execute("UPDATE inventory SET quantity = quantity - ? WHERE player_id = ? AND item_id = ?", (quantity, user_id, item_id))
        conn.commit()
        return True
    finally:
        conn.close()


def get_equipment(user_id):
    """Получить экипировку игрока."""
    conn = get_conn()
    try:
        row = conn.execute("SELECT weapon, armor, cosmetic FROM equipment WHERE player_id = ?", (user_id,)).fetchone()
        return dict(row) if row else {"weapon": None, "armor": None, "cosmetic": None}
    finally:
        conn.close()


def set_equipment(user_id, slot, item_id):
    """Установить экипировку."""
    conn = get_conn()
    try:
        conn.execute("INSERT OR IGNORE INTO equipment (player_id) VALUES (?)", (user_id,))
        conn.execute(f"UPDATE equipment SET {slot} = ? WHERE player_id = ?", (item_id, user_id))
        conn.commit()
    finally:
        conn.close()