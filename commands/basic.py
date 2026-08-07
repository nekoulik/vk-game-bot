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
        "🎮 Игровой бот\n\n"
        "Основные: старт, помощь, баланс, работа, ставка 50, дуэль, бонус, топ, профиль\n"
        "Магазин: магазин, инвентарь, купить <id>, экипировать <id>\n"
        "PvP: вызов @id123, статус дуэли, принять, отклонить\n"
        "Босс: босс, атака, статус, сдаться\n"
        "Прогресс: квесты, выполнить квесты, достижения\n"
        "Питомцы: питомцы, купить питомца <id>, мои питомцы, активировать <id>\n"
        "Сезоны: сезон, история сезонов\n"
        "Игры: игры, кнб <камень|ножницы|бумага>, угадай <число>, лотерея\n"
        "Кланы: клан, клан создать <название>, кланы, клан вступить <ID>\n"
        "Настройки: настройки, напоминания, включить <тип>, выключить <тип>"
    )
    send(api, peer_id, text)


def cmd_balance(api, peer_id, player):
    """Показать баланс."""
    send(api, peer_id, f"💰 Баланс: {player['balance']} монет.")


def cmd_profile(api, peer_id, player):
    """Показать профиль."""
    send(api, peer_id, 
         f"👤 {player['name']}\n"
         f"⭐ Уровень: {player['level']}\n"
         f"💰 Баланс: {player['balance']} монет\n"
         f"🏆 Очки сезона: {player['season_points']}")


def cmd_top(api, peer_id):
    """Показать топ игроков."""
    top = db.get_top_players(10)
    if not top:
        send(api, peer_id, "Пока нет игроков.")
        return
    
    lines = [" Топ игроков:\n"]
    for i, p in enumerate(top, start=1):
        lines.append(f"{i}. {p['name']} — {p['balance']}💰, ур. {p['level']}")
    
    send(api, peer_id, "\n".join(lines))


def cmd_work(api, peer_id, player):
    """Работа."""
    last_work = player.get("last_work")
    if last_work:
        last_time = datetime.fromisoformat(last_work)
        if (datetime.now() - last_time).seconds < 3600:
            send(api, peer_id, "⏰ Приходи через час!")
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
            send(api, peer_id, "⏰ Бонус уже получен! Приходи завтра.")
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
    - просто число 123
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
         f"⚔️ Дуэль принята!\n"
         f"Ставка: 50 монет с каждого\n"
         f"Напиши 'дуэль' чтобы начать бой!")


def cmd_decline_duel(api, peer_id, user_id):
    """Отклонить дуэль."""
    challenge = db.get_duel_challenge_for_user(user_id)
    
    if not challenge:
        send(api, peer_id, "📭 У тебя нет активных вызовов!")
        return
    
    db.clear_duel_challenge(challenge["id"])
    send(api, peer_id, " Дуэль отклонена.")


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


def cmd_duel(api, peer_id, user_id, player, command):
    """Дуэль — сначала проверяем PvP, потом с ботом."""
    # 1. Сначала проверяем активную PvP дуэль
    active_duel = db.get_active_duel(user_id)
    
    if active_duel:
        # PvP дуэль между игроками
        opponent_id = active_duel["player1_id"] if active_duel["player2_id"] == user_id else active_duel["player2_id"]
        stake = active_duel["stake"]
        
        # Бросок кубиков
        player_roll = random.randint(1, 6)
        opponent_roll = random.randint(1, 6)
        
        # Получаем имя противника
        opponent = db.get_player(opponent_id, lambda uid: get_name(api, uid))
        
        text = f"⚔️ PvP Дуэль!\n\n"
        text += f"🎯 Твой бросок: {player_roll}\n"
        text += f" {opponent['name']}: {opponent_roll}\n\n"
        
        if player_roll > opponent_roll:
            # Игрок выиграл
            win_amount = stake * 2
            db.add_coins_to_player(user_id, win_amount)
            db.end_duel(active_duel["id"], user_id)
            text += f"🎉 Ты выиграл {win_amount} монет!"
        elif player_roll < opponent_roll:
            # Противник выиграл
            db.add_coins_to_player(opponent_id, stake * 2)
            db.end_duel(active_duel["id"], opponent_id)
            text += f" {opponent['name']} выиграл {stake * 2} монет!"
        else:
            # Ничья — возвращаем ставки
            db.add_coins_to_player(user_id, stake)
            db.add_coins_to_player(opponent_id, stake)
            db.end_duel(active_duel["id"], None)
            text += f"🤝 Ничья! Ставки возвращены."
        
        send(api, peer_id, text)
        return
    
    # 2. Если нет PvP дуэли — дуэль с ботом
    parts = command.split()
    stake = 50  # По умолчанию
    
    if len(parts) > 1:
        try:
            stake = int(parts[1])
        except ValueError:
            send(api, peer_id, "❌ Неверная ставка! Формат: дуэль [ставка]")
            return
    
    if stake < 10:
        send(api, peer_id, " Минимальная ставка: 10 монет")
        return
    
    if player["balance"] < stake:
        send(api, peer_id, f"❌ Недостаточно монет! Нужно {stake}, у тебя {player['balance']}")
        return
    
    # Списываем ставку
    player["balance"] -= stake
    db.save_player(player)
    
    # Бросок
    player_roll = random.randint(1, 6)
    bot_roll = random.randint(1, 6)
    
    text = f" Дуэль с ботом!\n\n"
    text += f"🎯 Твой бросок: {player_roll}\n"
    text += f"🤖 Бросок бота: {bot_roll}\n\n"
    
    if player_roll > bot_roll:
        win = stake * 2
        player["balance"] += win
        db.save_player(player)
        text += f"🎉 Ты выиграл {win} монет!"
    elif player_roll < bot_roll:
        text += f"😔 Бот выиграл {stake} монет!"
    else:
        player["balance"] += stake
        db.save_player(player)
        text += f"🤝 Ничья! Ставка возвращена."
    
    send(api, peer_id, text)


def cmd_bet(api, peer_id, player, command):
    """Сделать ставку."""
    parts = command.split()
    try:
        stake = int(parts[1])
    except (IndexError, ValueError):
        send(api, peer_id, " Формат: ставка <сумма>")
        return
    
    if stake < 10:
        send(api, peer_id, " Минимальная ставка: 10 монет")
        return
    
    if player["balance"] < stake:
        send(api, peer_id, f"❌ Недостаточно монет! Нужно {stake}, у тебя {player['balance']}")
        return
    
    # Списываем ставку
    player["balance"] -= stake
    db.save_player(player)
    
    # Бросок
    player_roll = random.randint(1, 6)
    bot_roll = random.randint(1, 6)
    
    text = f"🎲 Ставка {stake} монет!\n\n"
    text += f"🎯 Твой бросок: {player_roll}\n"
    text += f"🤖 Бросок бота: {bot_roll}\n\n"
    
    if player_roll > bot_roll:
        win = stake * 2
        player["balance"] += win
        db.save_player(player)
        text += f"🎉 Ты выиграл {win} монет!"
    elif player_roll < bot_roll:
        text += f"😔 Бот выиграл {stake} монет!"
    else:
        player["balance"] += stake
        db.save_player(player)
        text += f"🤝 Ничья! Ставка возвращена."
    
    send(api, peer_id, text)