"""Проверки и валидация."""
import db


def is_admin(user_id, admin_ids):
    """Проверить, является ли пользователь админом."""
    return user_id in admin_ids


def is_banned(user_id):
    """Проверить, забанен ли пользователь."""
    return db.is_player_banned(user_id)


def has_enough_money(player, amount):
    """Проверить, достаточно ли у игрока монет."""
    return player["balance"] >= amount


def is_in_clan(user_id):
    """Проверить, состоит ли игрок в клане."""
    return db.get_clan(user_id) is not None