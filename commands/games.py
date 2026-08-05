"""
Команды мини-игр: КНБ, угадай число, лотерея.
"""
import random
import datetime
import db
from utils.helpers import send


def cmd_games_menu(api, peer_id):
    """Показать меню мини-игр."""
    text = (
        "🎮 Мини-игры:\n\n"
        "🪨 Камень-ножницы-бумага:\n"
        "  кнб <камень|ножницы|бумага>\n"
        "  Приз за победу: +10 монет\n\n"
        "🎲 Угадай число:\n"
        "  угадай <число от 1 до 10>\n"
        "  Приз: 50 монет\n\n"
        "🎫 Лотерея (100 монет):\n"
        "  лотерея\n"
        "  Шанс 30%, приз 200-500 монет"
    )
    send(api, peer_id, text)


def cmd_rps_menu(api, peer_id):
    """Показать правила КНБ."""
    send(api, peer_id, "🪨 Камень-ножницы-бумага!\n\nНапиши: кнб <камень|ножницы|бумага>")


def cmd_rps_play(api, peer_id, player, command):
    """Сыграть в камень-ножницы-бумага."""
    parts = command.split()
    if len(parts) < 2:
        send(api, peer_id, "Формат: кнб <камень|ножницы|бумага>")
        return
    
    player_choice = parts[1].lower()
    if player_choice not in ["камень", "ножницы", "бумага"]:
        send(api, peer_id, "Выбери: камень, ножницы или бумага")
        return
    
    bot_choice = random.choice(["камень", "ножницы", "бумага"])
    
    if player_choice == bot_choice:
        result = "🤝 Ничья!"
        db.add_season_points(player["user_id"], 1)
    elif (
        (player_choice == "камень" and bot_choice == "ножницы") or
        (player_choice == "ножницы" and bot_choice == "бумага") or
        (player_choice == "бумага" and bot_choice == "камень")
    ):
        result = "🏆 Ты победил! +10 монет"
        player["balance"] += 10
        db.add_season_points(player["user_id"], 2)
    else:
        result = " Бот победил! Попробуй ещё раз"
    
    db.save_player(player)
    send(api, peer_id, f"🪨 Камень-ножницы-бумага:\n\nТы: {player_choice}\nБот: {bot_choice}\n\n{result}")


def cmd_guess_menu(api, peer_id):
    """Показать правила игры 'Угадай число'."""
    send(api, peer_id, "🎲 Угадай число от 1 до 10!\n\nНапиши: угадай <число>")


def cmd_guess_play(api, peer_id, player, command):
    """Сыграть в 'Угадай число'."""
    parts = command.split()
    if len(parts) < 2:
        send(api, peer_id, "Формат: угадай <число от 1 до 10>")
        return
    
    try:
        guess = int(parts[1])
    except ValueError:
        send(api, peer_id, "Число должно быть от 1 до 10")
        return
    
    if guess < 1 or guess > 10:
        send(api, peer_id, "Число должно быть от 1 до 10")
        return
    
    secret = random.randint(1, 10)
    
    if guess == secret:
        reward = 50
        player["balance"] += reward
        db.save_player(player)
        db.add_season_points(player["user_id"], 5)
        send(api, peer_id, f"🎉 Угадал! Загаданное число: {secret}\nНаграда: +{reward} монет!")
    else:
        send(api, peer_id, f"😔 Не угадал! Загаданное число: {secret}\nТвоё число: {guess}\nПопробуй ещё раз: угадай <число>")


def cmd_lottery(api, peer_id, player):
    """Сыграть в лотерею."""
    last_lottery = player.get("last_lottery", "")
    today = datetime.date.today().isoformat()
    
    if last_lottery == today:
        send(api, peer_id, "🎫 Ты уже покупал лотерейный билет сегодня!\nПриходи завтра.")
        return
    
    ticket_price = 100
    if player["balance"] < ticket_price:
        send(api, peer_id, f"🎫 Билет стоит {ticket_price} монет.\nУ тебя недостаточно монет.")
        return
    
    player["balance"] -= ticket_price
    player["last_lottery"] = today
    
    if random.random() < 0.3:
        prize = random.randint(200, 500)
        player["balance"] += prize
        db.save_player(player)
        send(api, peer_id, f"🎉 ПОБЕДА В ЛОТЕРЕЕ!\n\nТы выиграл {prize} монет!\nЧистая прибыль: {prize - ticket_price} монет")
    else:
        db.save_player(player)
        send(api, peer_id, f"😔 Не повезло в лотерее...\n\nПопробуй завтра!")