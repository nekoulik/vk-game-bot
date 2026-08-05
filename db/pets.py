"""Функции для работы с питомцами."""
from datetime import datetime
from db.base import get_conn
from config.pets import PETS


def get_player_pets(user_id):
    """Получить всех питомцев игрока."""
    conn = get_conn()
    try:
        rows = conn.execute("SELECT pet_id, is_active FROM pets WHERE player_id = ?", (user_id,)).fetchall()
        return [{"pet_id": r["pet_id"], "is_active": bool(r["is_active"])} for r in rows]
    finally:
        conn.close()


def buy_pet(user_id, pet_id):
    """Купить питомца."""
    conn = get_conn()
    try:
        now = datetime.now().isoformat()
        conn.execute("INSERT OR IGNORE INTO pets (player_id, pet_id, is_active, acquired_at) VALUES (?, ?, 0, ?)", (user_id, pet_id, now))
        conn.commit()
        return conn.total_changes > 0
    finally:
        conn.close()


def activate_pet(user_id, pet_id):
    """Активировать питомца."""
    conn = get_conn()
    try:
        conn.execute("UPDATE pets SET is_active = 0 WHERE player_id = ?", (user_id,))
        conn.execute("UPDATE pets SET is_active = 1 WHERE player_id = ? AND pet_id = ?", (user_id, pet_id))
        conn.commit()
        return conn.total_changes > 0
    finally:
        conn.close()


def get_active_pet(user_id):
    """Получить ID активного питомца."""
    conn = get_conn()
    try:
        row = conn.execute("SELECT pet_id FROM pets WHERE player_id = ? AND is_active = 1", (user_id,)).fetchone()
        return row["pet_id"] if row else None
    finally:
        conn.close()


def get_pet_bonus(user_id, bonus_type):
    """Получить бонус от активного питомца."""
    active_pet_id = get_active_pet(user_id)
    if not active_pet_id or active_pet_id not in PETS:
        return 0.0
    pet = PETS[active_pet_id]
    return pet.get(f"bonus_{bonus_type}", 0.0)