"""
Команды квестов и достижений.
"""
import db
from utils.helpers import send


def cmd_quests(api, peer_id, player):
    """Показать статус ежедневных квестов."""
    status = db.get_daily_quests_status(player)
    send(api, peer_id, status)


def cmd_claim_quests(api, peer_id, player):
    """Забрать награды за выполненные квесты."""
    success, msg = db.claim_daily_quests(player)
    send(api, peer_id, msg)


def cmd_achievements(api, peer_id, user_id):
    """Показать список достижений игрока."""
    text = db.get_achievements_list(user_id)
    send(api, peer_id, text)