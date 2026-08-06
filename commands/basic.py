"""
Основные команды: помощь, баланс, работа, бонус, топ, профиль, PvP.
"""
import re
import random
from datetime import datetime
import db
from utils.helpers import send, get_name


def cmd_help(api, peer_id):
    """Показать помощь."""
    text = (
        " Игровой бот\n\n"
        "Основные: старт, помощь, баланс, работа, ставка 50, дуэль, бонус, топ, профиль\n"
        "Магазин: магазин, инвентарь, купить <id>, экипировать <id>\n"
        "PvP: вызов @id123, принять, отклонить\n"
        "Босс: босс, атака, статус, сдаться\n"
        "Прогресс: квесты, выполнить квесты, достижения\n"
        "Питомцы: питомцы, купить питомца <id>, мои питомцы, активировать <id>\n"
        "Сезоны: сезон, история сезонов\n"
        "Игры: игры, кнб <камень|ножницы|бумага>, угадай <число>, лотерея\n"
        "Кланы: клан, клан создать <название>, кланы, клан вступить <ID>"
    )
    send(api, peer_id, text)


def cmd_balance(api, peer_id, player):
    """Показать баланс."""
    send(api, peer_id, f"💰 Баланс: {player['balance']} монет.")


def cmd_profile(api, peer_id, player):
    """Показать профиль."""
    send(api, peer_id, 
         f" {player['name']}\n"
         f"⭐ Уровень: {player['level']}\n"
         f"💰 Баланс: {player['balance']} монет\n"
         f"🏆 Очки сезона: {player['season_points']}")


def cmd_top(api, peer_id):
    """Показать топ игроков."""
    top = db.get_top_players(10)
    if not top:
        send(api, peer_id, "Пока нет игроков.")
        return
    
    lines = ["🏆 Топ игроков:\n"]
    for i, p in enumerate(top, start=1):
        lines.append(f"{i}. {p['name']} — {p['balance']}💰, ур. {p['level']}")
    
    send(api, peer_id, "\n".join(lines))


def cmd_work(api, peer_id, player):
    """Работа."""
    last_work = player.get("last_work")
    if last_work:
        last_time = datetime.fromisoformat(last_work)
        if (datetime.now() - last_time).seconds < 3600:
            send(api, peer_id, " Приходи через час!")
            return
    
    earnings = random.randint(50, 150) * player["level"]
    player["balance"] += earnings
    player["last_work"] = datetime.now().isoformat()
    db.save_player(player)
    
    send(api, peer_id, f"💼 Ты поработал и заработал {earnings} монет!")


def cmd_bonus(api, peer_id, player):
    """Ежедневный бонус."""
    last_bonus = player.get("last_bonus")
    if last_bonus:
        last_time = datetime.fromisoformat(last_bonus)
        if (datetime.now() - last_time).seconds < 86400:
            send(api, peer_id, " Бонус уже получен! Приходи завтра.")
            return
    
    bonus = 100 * player["level"]
    player["balance"] += bonus
    player["last_bonus"] = datetime.now().isoformat()
    db.save_player(player)
    
    send(api, peer_id, f"🎁 Ты получил {bonus} монет!")


# ============ PvP ФУНКЦИИ ============

def _parse_user_id(text):
    """
    Извлечь ID пользователя из текста.
    Поддерживает форматы:
    - @id123
    - [id123|Имя]
    - [club123|Название]
    - просто число 123
    Возвращает user_id или None.
    """
    # Формат [id123|Имя] — стандартное упоминание VK
    match = re.search(r'\[id(\d+)[^\]]*\]', text)
    if match:
        return int(match.group(1))
    
    # Формат @id123
    match = re.search(r'@id(\d+)', text)
    if match:
        return int(match.group(1))
    
    # Просто число
    match = re.search(r'^(\d+)$', text.strip())
    if match:
        return int(match.group(1))
    
    return None


def cmd_challenge(api, peer_id, user_id, text):
    """Вызвать на дуэль."""
    # Ищем ID в ОРИГИНАЛЬНОМ тексте (не в command.lower())
    target_id = _parse_user_id(text)
    
    if not target_id:
        send(api, peer_id, "⚔️ Формат: вызов @id123")
        return
    
    if target_id == user_id:
        send(api, peer_id, "❌ Нельзя вызвать самого себя!")
        return
    
    # Проверяем баланс
    player = db.get_player(user_id, lambda uid: get_name(api, uid))
    if player["balance"] < 50:
        send(api, peer_id, "❌ Нужно минимум 50 монет для вызова!")
        return
    
    # Создаём вызов в БД
    db.create_duel_challenge(user_id, target_id)
    
    send(api, peer_id, f"⚔️ Вызов отправлен пользователю {target_id}!\nОни должны написать 'принять' или 'отклонить'.")


def cmd_accept_duel(api, peer_id, user_id, player):
    """Принять дуэль."""
    challenge = db.get_duel_challenge_for_user(user_id)
    
    if not challenge:
        send(api, peer_id, "❌ У тебя нет активных вызовов!")
        return
    
    challenger_id = challenge["challenger_id"]
    
    # Проверяем баланс
    if player["balance"] < 50:
        send(api, peer_id, "❌ Нужно минимум 50 монет для дуэли!")
        return
    
    # Списываем ставку с обоих
    db.add_coins_to_player(challenger_id, -50)
    db.add_coins_to_player(user_id, -50)
    
    # Начинаем дуэль
    db.start_duel(challenger_id, user_id, 50)
    db.clear_duel_challenge(challenge["id"])
    
    send(api, peer_id, 
         f"️ Дуэль принята!\n"
         f"Ставка: 50 монет с каждого\n"
         f"Напиши 'дуэль' чтобы начать бой!")


def cmd_decline_duel(api, peer_id, user_id):
    """Отклонить дуэль."""
    challenge = db.get_duel_challenge_for_user(user_id)
    
    if not challenge:
        send(api, peer_id, "📭 У тебя нет активных вызовов!")
        return
    
    db.clear_duel_challenge(challenge["id"])
    send(api, peer_id, "❌ Дуэль отклонена.")


def cmd_duel_status(api, peer_id, user_id):
    """Проверить статус дуэли."""
    challenges = db.get_duel_challenges_for_user(user_id)
    
    if not challenges:
        send(api, peer_id, "📭 У тебя нет активных вызовов.")
        return
    
    lines = ["⚔️ Активные вызовы:\n"]
    for c in challenges:
        lines.append(f"• От игрока с ID {c['challenger_id']}")
    
    lines.append("\nНапиши 'принять' или 'отклонить'")
    send(api, peer_id, "\n".join(lines))


def cmd_duel(api, peer_id, user_id, player):
    """Начать/провести дуэль."""
    duel = db.get_active_duel(user_id)
    
    if not duel:
        send(api, peer_id, "❌ У тебя нет активной дуэли!")
        return
    
    # Простая механика: рандомный победитель
    winner_id = random.choice([duel["player1_id"], duel["player2_id"]])
    
    # Выдаём награду (ставка * 2 = 100 монет)
    prize = duel["stake"] * 2
    db.add_coins_to_player(winner_id, prize)
    
    # Завершаем дуэль
    db.end_duel(duel["id"], winner_id)
    
    winner = db.get_player(winner_id, lambda uid: get_name(api, uid))
    
    if winner_id == user_id:
        send(api, peer_id, f"🎉 Ты выиграл дуэль! +{prize} монет")
    else:
        send(api, peer_id, f"😔 Ты проиграл дуэль. Победитель: {winner['name']} (+{prize} монет)")