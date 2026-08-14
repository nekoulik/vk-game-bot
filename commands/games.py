"""
Мини-игры для бота.
"""
import random
from utils.helpers import send, format_number
import db


def cmd_games_menu(api, peer_id):
    """Показать меню игр."""
    text = (
        "🎮 *Мини-игры:*\n\n"
        "1️ *Камень-ножницы-бумага*\n"
        "   Формат: кнб <камень|ножницы|бумага>\n"
        "   Ставка: 50 монет\n\n"
        "2️⃣ *Угадай число*\n"
        "   Формат: число <число от 1 до 10>\n"
        "   Ставка: 30 монет\n"
        "   Выигрыш: x2\n\n"
        "3️⃣ *Рулетка*\n"
        "   Формат: рулетка <красное|черное|число>\n"
        "   Ставка: 100 монет\n"
        "   Выигрыш: x2 (на цвет) или x10 (на число)\n\n"
        "4️⃣ *Монетка*\n"
        "   Формат: монетка <орёл|решка>\n"
        "   Ставка: 50 монет"
    )
    send(api, peer_id, text)


def cmd_rps(api, peer_id, player, command):
    """Камень-ножницы-бумага."""
    parts = command.split()
    
    if len(parts) < 2:
        send(api, peer_id, " Формат: кнб <камень|ножницы|бумага>\nПример: кнб камень")
        return
    
    choice = parts[1].lower()
    valid_choices = ["камень", "ножницы", "бумага"]
    
    if choice not in valid_choices:
        send(api, peer_id, "❌ Выбери: камень, ножницы или бумага")
        return
    
    balance = int(player.get("balance", 0))
    bet = 50
    
    if balance < bet:
        send(api, peer_id, f"❌ Недостаточно монет! Нужно {bet}, у тебя {balance}")
        return
    
    # Выбор бота
    bot_choice = random.choice(valid_choices)
    
    # Определяем победителя
    if choice == bot_choice:
        result = " Ничья!"
        reward = 0
    elif (
        (choice == "камень" and bot_choice == "ножницы") or
        (choice == "ножницы" and bot_choice == "бумага") or
        (choice == "бумага" and bot_choice == "камень")
    ):
        result = f"🎉 Ты выиграл! +{bet} монет"
        reward = bet
    else:
        result = f"😔 Ты проиграл! -{bet} монет"
        reward = -bet
    
    # Обновляем баланс
    player["balance"] = balance + reward
    db.save_player(player)
    
    # Эмодзи для выбора
    emojis = {"камень": "🪨", "ножницы": "✂️", "бумага": "📄"}
    
    text = (
        f" *Камень-ножницы-бумага*\n\n"
        f" Твой выбор: {emojis[choice]} {choice}\n"
        f"🤖 Выбор бота: {emojis[bot_choice]} {bot_choice}\n\n"
        f"{result}\n"
        f"💰 Баланс: {format_number(player['balance'])}"
    )
    send(api, peer_id, text)


def cmd_guess_number(api, peer_id, player, command):
    """Угадай число."""
    parts = command.split()
    
    if len(parts) < 2:
        send(api, peer_id, "🎮 Формат: число <число от 1 до 10>\nПример: число 7")
        return
    
    try:
        guess = int(parts[1])
    except ValueError:
        send(api, peer_id, "❌ Введи число от 1 до 10")
        return
    
    if guess < 1 or guess > 10:
        send(api, peer_id, "❌ Число должно быть от 1 до 10")
        return
    
    balance = int(player.get("balance", 0))
    bet = 30
    
    if balance < bet:
        send(api, peer_id, f"❌ Недостаточно монет! Нужно {bet}, у тебя {balance}")
        return
    
    # Загадываем число
    secret_number = random.randint(1, 10)
    
    if guess == secret_number:
        reward = bet * 2
        player["balance"] = balance + reward
        result = f"🎉 Угадал! Загаданное число: {secret_number}\n+{reward} монет!"
    else:
        reward = -bet
        player["balance"] = balance + reward
        result = f"😔 Не угадал! Загаданное число: {secret_number}\n-{bet} монет"
    
    db.save_player(player)
    
    text = (
        f"🎮 *Угадай число*\n\n"
        f"👤 Твой выбор: {guess}\n"
        f"🤖 Загаданное число: {secret_number}\n\n"
        f"{result}\n"
        f"💰 Баланс: {format_number(player['balance'])}"
    )
    send(api, peer_id, text)


def cmd_roulette(api, peer_id, player, command):
    """Рулетка."""
    parts = command.split()
    
    if len(parts) < 2:
        send(api, peer_id, "🎰 Формат: рулетка <красное|черное|число>\nПример: рулетка красное")
        return
    
    bet_choice = parts[1].lower()
    balance = int(player.get("balance", 0))
    bet = 100
    
    if balance < bet:
        send(api, peer_id, f"❌ Недостаточно монет! Нужно {bet}, у тебя {balance}")
        return
    
    # Генерируем число от 0 до 10
    number = random.randint(0, 10)
    
    # Определяем цвет (нечётные - красные, чётные - чёрные, 0 - зелёное)
    if number == 0:
        color = "зелёное"
    elif number % 2 == 0:
        color = "черное"
    else:
        color = "красное"
    
    reward = 0
    win = False
    
    # Проверяем выигрыш
    if bet_choice in ["красное", "красный"]:
        if color == "красное":
            win = True
            reward = bet  # x2
    elif bet_choice in ["черное", "черный"]:
        if color == "черное":
            win = True
            reward = bet  # x2
    else:
        # Игрок поставил на число
        try:
            bet_number = int(bet_choice)
            if bet_number == number:
                win = True
                reward = bet * 9  # x10
        except ValueError:
            send(api, peer_id, "❌ Ставка: красное, черное или число (0-10)")
            return
    
    if win:
        player["balance"] = balance + reward
        result = f" Выигрыш! +{reward} монет"
    else:
        player["balance"] = balance - bet
        result = f"😔 Проигрыш! -{bet} монет"
    
    db.save_player(player)
    
    # Эмодзи для цвета
    color_emojis = {"красное": "🔴", "черное": "⚫", "зелёное": "🟢"}
    
    text = (
        f"🎰 *Рулетка*\n\n"
        f"👤 Твоя ставка: {bet_choice}\n"
        f"🎲 Выпало: {color_emojis.get(color, '')} {color} ({number})\n\n"
        f"{result}\n"
        f"💰 Баланс: {format_number(player['balance'])}"
    )
    send(api, peer_id, text)


def cmd_coin(api, peer_id, player, command):
    """Монетка (орёл или решка)."""
    parts = command.split()
    
    if len(parts) < 2:
        send(api, peer_id, "🪙 Формат: монетка <орёл|решка>\nПример: монетка орёл")
        return
    
    choice = parts[1].lower()
    
    if choice not in ["орёл", "орел", "решка"]:
        send(api, peer_id, "❌ Выбери: орёл или решка")
        return
    
    balance = int(player.get("balance", 0))
    bet = 50
    
    if balance < bet:
        send(api, peer_id, f"❌ Недостаточно монет! Нужно {bet}, у тебя {balance}")
        return
    
    # Подбрасываем монетку
    result_coin = random.choice(["орёл", "решка"])
    
    if choice in ["орёл", "орел"] and result_coin == "орёл":
        win = True
    elif choice == "решка" and result_coin == "решка":
        win = True
    else:
        win = False
    
    if win:
        player["balance"] = balance + bet
        result = f" Угадал! +{bet} монет"
    else:
        player["balance"] = balance - bet
        result = f"😔 Не угадал! -{bet} монет"
    
    db.save_player(player)
    
    emojis = {"орёл": "", "решка": "🪙"}
    
    text = (
        f" *Монетка*\n\n"
        f"👤 Твой выбор: {emojis.get(choice, '')} {choice}\n"
        f"🎲 Выпало: {emojis[result_coin]} {result_coin}\n\n"
        f"{result}\n"
        f"💰 Баланс: {format_number(player['balance'])}"
    )
    send(api, peer_id, text)